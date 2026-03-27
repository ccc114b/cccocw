use crate::tensor::{
    add, arr1, matmul as tensor_matmul, relu, rmsnorm as tensor_rmsnorm, scalar,
    softmax as tensor_softmax, zeros, TensorPool,
};
use ndarray::{Array, ArrayD, IxDyn};
use rand::Rng;

pub struct Linear {
    pub w_id: usize,
    pub b_id: usize,
    nin: usize,
    nout: usize,
}

impl Linear {
    pub fn new(nin: usize, nout: usize, pool: &mut TensorPool) -> Self {
        let mut rng = rand::thread_rng();
        let scale = (2.0 / nin as f64).sqrt();

        let w_data: Vec<f64> = (0..nin * nout).map(|_| rng.gen::<f64>() * scale).collect();
        let w = Array::from_shape_vec(IxDyn(&[nout, nin]), w_data)
            .unwrap()
            .into_dyn();
        let w_id = pool.alloc(w, vec![]);

        let b = zeros(&[nout]);
        let b_id = pool.alloc(b, vec![]);

        Self {
            w_id,
            b_id,
            nin,
            nout,
        }
    }

    pub fn forward(&self, x_id: usize, pool: &mut TensorPool) -> usize {
        eprintln!(
            "DEBUG Linear forward: x_id={}, x shape={:?}, w shape={:?}",
            x_id,
            pool.get(x_id).data.shape(),
            pool.get(self.w_id).data.shape()
        );
        let wx_id = tensor_matmul(self.w_id, x_id, pool);
        eprintln!(
            "DEBUG Linear forward: wx_id={}, wx shape={:?}",
            wx_id,
            pool.get(wx_id).data.shape()
        );
        let result = add(wx_id, self.b_id, pool);
        eprintln!(
            "DEBUG Linear forward: result shape={:?}",
            pool.get(result).data.shape()
        );
        result
    }

    pub fn params(&self) -> Vec<usize> {
        vec![self.w_id, self.b_id]
    }
}

pub struct RMSNorm {
    pub x_id: usize,
    dim: usize,
}

impl RMSNorm {
    pub fn new(dim: usize, pool: &mut TensorPool) -> Self {
        let x_id = pool.alloc(zeros(&[dim]), vec![]);
        Self { x_id, dim }
    }

    pub fn forward(&self, x_id: usize, pool: &mut TensorPool) -> usize {
        tensor_rmsnorm(x_id, pool)
    }
}

pub struct MultiHeadAttention {
    pub wq: Linear,
    pub wk: Linear,
    pub wv: Linear,
    pub wo: Linear,
    n_head: usize,
    head_dim: usize,
}

impl MultiHeadAttention {
    pub fn new(n_embd: usize, n_head: usize, pool: &mut TensorPool) -> Self {
        Self {
            wq: Linear::new(n_embd, n_embd, pool),
            wk: Linear::new(n_embd, n_embd, pool),
            wv: Linear::new(n_embd, n_embd, pool),
            wo: Linear::new(n_embd, n_embd, pool),
            n_head,
            head_dim: n_embd,
        }
    }

    pub fn forward(
        &self,
        x_id: usize,
        keys: &mut Vec<Vec<usize>>,
        values: &mut Vec<Vec<usize>>,
        pool: &mut TensorPool,
        head_idx: usize,
    ) -> usize {
        eprintln!(
            "DEBUG attn forward: x_id={}, x shape={:?}",
            x_id,
            pool.get(x_id).data.shape()
        );
        let q_id = self.wq.forward(x_id, pool);
        eprintln!(
            "DEBUG attn forward: q_id={}, q shape={:?}",
            q_id,
            pool.get(q_id).data.shape()
        );
        let k_id = self.wk.forward(x_id, pool);
        let v_id = self.wv.forward(x_id, pool);

        keys[head_idx].push(k_id);
        values[head_idx].push(v_id);

        let n_ctx = keys[head_idx].len();
        eprintln!("DEBUG attn forward: n_ctx={}", n_ctx);

        let mut attn_id = None;
        for t in 0..n_ctx {
            let logits_vec: Vec<f64> = (0..self.head_dim).map(|_| 0.0).collect();
            let mut logits_id = pool.alloc(ndarray::arr1(&logits_vec).into_dyn(), vec![]);
            for j in 0..self.head_dim {
                let q_idx = j;
                let k_idx = j;
                let q_val = pool.get(q_id).data[[q_idx]];
                let k_val = pool.get(keys[head_idx][t]).data[[k_idx]];
                let prod_id = pool.alloc(
                    scalar(q_val * k_val / (self.head_dim as f64).sqrt()),
                    vec![],
                );
                logits_id = add(logits_id, prod_id, pool);
            }
            let attn_weights_id = tensor_softmax(logits_id, pool);
            let out_vec: Vec<f64> = (0..self.head_dim).map(|_| 0.0).collect();
            let mut out_id = pool.alloc(ndarray::arr1(&out_vec).into_dyn(), vec![]);
            for t in 0..n_ctx {
                for j in 0..self.head_dim {
                    let w = pool.get(attn_weights_id).data[[t]];
                    let v_val = pool.get(values[head_idx][t]).data[[j]];
                    out_id = add(out_id, pool.alloc(scalar(w * v_val), vec![]), pool);
                }
            }
            attn_id = Some(out_id);
        }

        let attn_id = attn_id.unwrap_or(x_id);
        self.wo.forward(attn_id, pool)
    }

    pub fn params(&self) -> Vec<usize> {
        let mut p = self.wq.params();
        p.extend(self.wk.params());
        p.extend(self.wv.params());
        p.extend(self.wo.params());
        p
    }
}

pub struct MLP {
    pub fc1: Linear,
    pub fc2: Linear,
}

impl MLP {
    pub fn new(n_embd: usize, pool: &mut TensorPool) -> Self {
        Self {
            fc1: Linear::new(n_embd, 4 * n_embd, pool),
            fc2: Linear::new(4 * n_embd, n_embd, pool),
        }
    }

    pub fn forward(&self, x_id: usize, pool: &mut TensorPool) -> usize {
        eprintln!(
            "DEBUG MLP forward: x_id={}, x shape={:?}",
            x_id,
            pool.get(x_id).data.shape()
        );
        let hidden_id = self.fc1.forward(x_id, pool);
        eprintln!(
            "DEBUG MLP forward: hidden_id={}, hidden shape={:?}",
            hidden_id,
            pool.get(hidden_id).data.shape()
        );
        let hidden_relu_id = relu(hidden_id, pool);
        eprintln!(
            "DEBUG MLP forward: hidden_relu_id={}, relu shape={:?}",
            hidden_relu_id,
            pool.get(hidden_relu_id).data.shape()
        );
        let result = self.fc2.forward(hidden_relu_id, pool);
        eprintln!(
            "DEBUG MLP forward: fc2 result shape={:?}",
            pool.get(result).data.shape()
        );
        result
    }

    pub fn params(&self) -> Vec<usize> {
        let mut p = self.fc1.params();
        p.extend(self.fc2.params());
        p
    }
}

pub struct GPTBlock {
    pub attn: MultiHeadAttention,
    pub mlp: MLP,
    n_embd: usize,
}

impl GPTBlock {
    pub fn new(n_embd: usize, n_head: usize, pool: &mut TensorPool) -> Self {
        Self {
            attn: MultiHeadAttention::new(n_embd, n_head, pool),
            mlp: MLP::new(n_embd, pool),
            n_embd,
        }
    }

    pub fn forward(
        &self,
        x_id: usize,
        keys: &mut Vec<Vec<usize>>,
        values: &mut Vec<Vec<usize>>,
        layer_idx: usize,
        pool: &mut TensorPool,
    ) -> usize {
        eprintln!(
            "DEBUG GPTBlock forward: x_id={}, x shape={:?}",
            x_id,
            pool.get(x_id).data.shape()
        );
        let x_residual_id = x_id;

        eprintln!("DEBUG GPTBlock forward: calling attn.forward");
        let attn_out_id = self.attn.forward(x_id, keys, values, pool, layer_idx);
        eprintln!(
            "DEBUG GPTBlock forward: attn_out_id={}, shape={:?}",
            attn_out_id,
            pool.get(attn_out_id).data.shape()
        );

        let combined_id = add(attn_out_id, x_residual_id, pool);
        eprintln!(
            "DEBUG GPTBlock forward: combined_id={}, shape={:?}",
            combined_id,
            pool.get(combined_id).data.shape()
        );

        let mlp_out_id = self.mlp.forward(combined_id, pool);
        eprintln!(
            "DEBUG GPTBlock forward: mlp_out_id={}, shape={:?}",
            mlp_out_id,
            pool.get(mlp_out_id).data.shape()
        );

        add(mlp_out_id, combined_id, pool)
    }

    pub fn params(&self) -> Vec<usize> {
        let mut p = self.attn.params();
        p.extend(self.mlp.params());
        p
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tensor::{backward, exp};

    #[test]
    #[ignore]
    fn test_linear_forward() {
        let mut pool = TensorPool::new();
        let linear = Linear::new(4, 2, &mut pool);
        let x_id = pool.alloc(arr1(&[1.0, 2.0, 3.0, 4.0]).into_dyn(), vec![]);
        let y_id = linear.forward(x_id, &mut pool);

        assert_eq!(pool.get(y_id).data.shape()[0], 2);
    }

    #[test]
    #[ignore]
    fn test_mlp_forward() {
        let mut pool = TensorPool::new();
        let mlp = MLP::new(4, &mut pool);
        let x_id = pool.alloc(arr1(&[1.0, 2.0, 3.0, 4.0]).into_dyn(), vec![]);
        let y_id = mlp.forward(x_id, &mut pool);

        assert_eq!(pool.get(y_id).data.shape()[0], 4);
    }
}
