use ndarray::{Array, ArrayD, IxDyn};

pub use ndarray::arr1;

#[derive(Clone)]
pub struct Value {
    pub data: ArrayD<f64>,
    pub grad: Option<ArrayD<f64>>,
    pub children: Vec<ChildInfo>,
    pub id: usize,
}

#[derive(Clone)]
pub struct ChildInfo {
    pub id: usize,
    pub local_grad: ArrayD<f64>,
}

pub struct TensorPool {
    pub tensors: Vec<Value>,
    pub counter: usize,
}

impl TensorPool {
    pub fn new() -> Self {
        Self {
            tensors: Vec::new(),
            counter: 0,
        }
    }

    pub fn alloc(&mut self, data: ArrayD<f64>, children: Vec<ChildInfo>) -> usize {
        let id = self.counter;
        self.counter += 1;
        self.tensors.push(Value {
            data,
            grad: None,
            children,
            id,
        });
        id
    }

    pub fn get(&self, id: usize) -> &Value {
        &self.tensors[id]
    }

    pub fn get_mut(&mut self, id: usize) -> &mut Value {
        &mut self.tensors[id]
    }

    pub fn len(&self) -> usize {
        self.tensors.len()
    }

    pub fn get_grad(&self, id: usize) -> Option<&ArrayD<f64>> {
        self.tensors[id].grad.as_ref()
    }

    pub fn set_grad(&mut self, id: usize, grad: ArrayD<f64>) {
        self.tensors[id].grad = Some(grad);
    }

    pub fn take_grad(&mut self, id: usize) -> Option<ArrayD<f64>> {
        self.tensors[id].grad.take()
    }
}

impl Default for TensorPool {
    fn default() -> Self {
        Self::new()
    }
}

pub fn scalar(data: f64) -> ArrayD<f64> {
    Array::from_elem(IxDyn(&[]), data)
}

pub fn zeros(shape: &[usize]) -> ArrayD<f64> {
    Array::zeros(IxDyn(shape))
}

pub fn ones(shape: &[usize]) -> ArrayD<f64> {
    Array::ones(IxDyn(shape))
}

pub fn add(a_id: usize, b_id: usize, pool: &mut TensorPool) -> usize {
    let a = pool.get(a_id).data.clone();
    let b = pool.get(b_id).data.clone();
    let a_shape = a.shape();
    let b_shape = b.shape();

    let data = if a_shape.len() == 1 && b_shape.len() == 1 {
        if a_shape[0] == b_shape[0] {
            &a + &b
        } else {
            a + b
        }
    } else if a_shape.len() == 1 && b_shape.is_empty() {
        let b_scalar = b[[]];
        let mut result = Array::zeros(IxDyn(a_shape));
        for i in 0..a_shape[0] {
            result[[i]] = a[[i]] + b_scalar;
        }
        result
    } else if b_shape.len() == 1 && a_shape.is_empty() {
        let a_scalar = a[[]];
        let mut result = Array::zeros(IxDyn(b_shape));
        for i in 0..b_shape[0] {
            result[[i]] = b[[i]] + a_scalar;
        }
        result
    } else if a_shape.is_empty() && b_shape.is_empty() {
        scalar(a[[]] + b[[]])
    } else {
        &a + &b
    };

    let children = vec![
        ChildInfo {
            id: b_id,
            local_grad: scalar(1.0),
        },
        ChildInfo {
            id: a_id,
            local_grad: scalar(1.0),
        },
    ];
    pool.alloc(data, children)
}

pub fn mul(a_id: usize, b_id: usize, pool: &mut TensorPool) -> usize {
    let a = pool.get(a_id).data.clone();
    let b = pool.get(b_id).data.clone();
    let data = &a * &b;
    let children = vec![
        ChildInfo {
            id: a_id,
            local_grad: b.clone(),
        },
        ChildInfo {
            id: b_id,
            local_grad: a.clone(),
        },
    ];
    pool.alloc(data, children)
}

pub fn relu(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.max(0.0));
    let mask = x.mapv(|v| if v > 0.0 { 1.0 } else { 0.0 });
    let children = vec![ChildInfo {
        id: x_id,
        local_grad: mask,
    }];
    pool.alloc(data, children)
}

pub fn log(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.ln());
    let inv_x = x.mapv(|v| 1.0 / v);
    let children = vec![ChildInfo {
        id: x_id,
        local_grad: inv_x,
    }];
    pool.alloc(data, children)
}

pub fn exp(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let exp_data = x.mapv(|v| v.exp());
    let children = vec![ChildInfo {
        id: x_id,
        local_grad: exp_data.clone(),
    }];
    pool.alloc(exp_data, children)
}

pub fn pow(x_id: usize, exp: f64, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.powf(exp));
    let grad = x.mapv(|v| exp * v.powf(exp - 1.0));
    let children = vec![ChildInfo {
        id: x_id,
        local_grad: grad,
    }];
    pool.alloc(data, children)
}

pub fn matmul(a_id: usize, b_id: usize, pool: &mut TensorPool) -> usize {
    let a_orig = pool.get(a_id).data.clone();
    let b_orig = pool.get(b_id).data.clone();
    let a_shape = a_orig.shape();
    let b_shape = b_orig.shape();

    let a = a_orig.clone();
    let b = b_orig.clone();

    let a_for_grad = a_orig.clone();
    let b_for_grad = b_orig.clone();

    let data = if a_shape.len() == 2 && b_shape.len() == 2 {
        if a_shape[1] != b_shape[0] {
            panic!(
                "matmul dimension mismatch: a[1]={} != b[0]={}",
                a_shape[1], b_shape[0]
            );
        }
        let mut result = Array::zeros(IxDyn(&[a_shape[0], b_shape[1]]));
        for i in 0..a_shape[0] {
            for j in 0..b_shape[1] {
                let mut sum = 0.0;
                for k in 0..a_shape[1] {
                    sum += a[[i, k]] * b[[k, j]];
                }
                result[[i, j]] = sum;
            }
        }
        result
    } else if a_shape.len() == 2 && b_shape.len() == 1 {
        if a_shape[1] != b_shape[0] {
            panic!(
                "matmul dimension mismatch: a[1]={} != b[0]={}",
                a_shape[1], b_shape[0]
            );
        }
        let mut result = Array::zeros(IxDyn(&[a_shape[0]]));
        for i in 0..a_shape[0] {
            let mut sum = 0.0;
            for k in 0..a_shape[1] {
                sum += a[[i, k]] * b[[k]];
            }
            result[[i]] = sum;
        }
        result
    } else if a_shape.len() == 1 && b_shape.len() == 1 {
        let mut sum = 0.0;
        for k in 0..a_shape[0] {
            sum += a[[k]] * b[[k]];
        }
        Array::from_elem(IxDyn(&[]), sum)
    } else {
        a * b
    };

    let local_grad_a = if a_shape.len() == 2 && b_shape.len() == 1 {
        let nout = a_shape[0];
        let nin = a_shape[1];
        let mut lg = Array::zeros(IxDyn(&[nout, nin]));
        for i in 0..nout {
            for j in 0..nin {
                lg[[i, j]] = b_for_grad[[i]] * a_for_grad[[i, j]];
            }
        }
        lg
    } else if a_shape.len() == 2 && b_shape.len() == 2 {
        b_for_grad.t().to_owned()
    } else if a_shape.len() == 1 && b_shape.len() == 1 {
        b_for_grad.clone()
    } else {
        b_for_grad.t().to_owned()
    };

    let local_grad_b = if a_shape.len() == 2 && b_shape.len() == 1 {
        a_for_grad.t().to_owned()
    } else if a_shape.len() == 2 && b_shape.len() == 2 {
        a_for_grad.t().to_owned()
    } else if a_shape.len() == 1 && b_shape.len() == 1 {
        a_for_grad.clone()
    } else {
        a_for_grad.t().to_owned()
    };

    let children = vec![
        ChildInfo {
            id: a_id,
            local_grad: local_grad_a,
        },
        ChildInfo {
            id: b_id,
            local_grad: local_grad_b,
        },
    ];
    pool.alloc(data, children)
}

pub fn softmax(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let x_shape = x.shape();

    let data = if x_shape.len() == 1 {
        let len = x_shape[0];
        let max_val = x.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let mut sum_exp = 0.0;
        let mut result = Array::zeros(IxDyn(&[len]));
        for i in 0..len {
            let exp_val = (x[[i]] - max_val).exp();
            result[[i]] = exp_val;
            sum_exp += exp_val;
        }
        for i in 0..len {
            result[[i]] /= sum_exp;
        }
        result
    } else {
        x.mapv(|v| v.exp())
    };

    let local_grad = data.clone();
    let children = vec![ChildInfo {
        id: x_id,
        local_grad,
    }];
    pool.alloc(data, children)
}

pub fn rmsnorm(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let x_shape = x.shape().to_vec();

    let data = if x_shape.len() == 1 {
        let len = x_shape[0];
        let ms: f64 = x.iter().map(|v| v * v).sum::<f64>() / len as f64;
        let scale = (ms + 1e-5).powf(-0.5);
        x.mapv(|v| v * scale)
    } else {
        x
    };

    let local_grad = ones(&x_shape);
    let children = vec![ChildInfo {
        id: x_id,
        local_grad,
    }];
    pool.alloc(data, children)
}

pub fn cross_entropy(logits_id: usize, target_id: usize, pool: &mut TensorPool) -> usize {
    let logits = pool.get(logits_id).data.clone();
    let target = pool.get(target_id).data.clone();
    let vocab_size = logits.shape()[0];
    let target_idx = target[[]] as usize;

    let max_val = logits.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
    let mut sum_exp = 0.0;
    for i in 0..vocab_size {
        sum_exp += (logits[[i]] - max_val).exp();
    }
    let loss = sum_exp.ln() - (logits[[target_idx]] - max_val);

    let data = scalar(loss);
    let local_grad = scalar(1.0);
    let children = vec![
        ChildInfo {
            id: logits_id,
            local_grad: local_grad.clone(),
        },
        ChildInfo {
            id: target_id,
            local_grad,
        },
    ];
    pool.alloc(data, children)
}

pub struct Adam {
    pub params: Vec<usize>,
    pub lr: f64,
    beta1: f64,
    beta2: f64,
    eps: f64,
    m: Vec<f64>,
    v: Vec<f64>,
    step_count: usize,
}

impl Adam {
    pub fn new(params: Vec<usize>, lr: f64, beta1: f64, beta2: f64, eps: f64) -> Self {
        let m = vec![0.0; params.len()];
        let v = vec![0.0; params.len()];
        Self {
            params,
            lr,
            beta1,
            beta2,
            eps,
            m,
            v,
            step_count: 0,
        }
    }

    pub fn step(&mut self, pool: &mut TensorPool, lr_override: Option<f64>) {
        self.step_count += 1;
        let lr = lr_override.unwrap_or(self.lr);

        for (i, &param_id) in self.params.iter().enumerate() {
            let grad = match pool.get_grad(param_id) {
                Some(g) => g[[]],
                None => 0.0,
            };

            self.m[i] = self.beta1 * self.m[i] + (1.0 - self.beta1) * grad;
            self.v[i] = self.beta2 * self.v[i] + (1.0 - self.beta2) * grad * grad;

            let m_hat = self.m[i] / (1.0 - self.beta1.powi(self.step_count as i32));
            let v_hat = self.v[i] / (1.0 - self.beta2.powi(self.step_count as i32));

            let new_data = pool.get(param_id).data[[]] - lr * m_hat / (v_hat.powf(0.5) + self.eps);
            pool.get_mut(param_id).data = scalar(new_data);
            pool.get_mut(param_id).grad = None;
        }
    }
}

pub fn backward(root_id: usize, pool: &mut TensorPool) {
    let n = pool.len();
    let mut visited = vec![false; n];
    let mut topo: Vec<usize> = Vec::new();

    fn build_topo(pool: &TensorPool, v: usize, visited: &mut Vec<bool>, topo: &mut Vec<usize>) {
        if visited[v] {
            return;
        }
        visited[v] = true;
        for child in &pool.get(v).children {
            build_topo(pool, child.id, visited, topo);
        }
        topo.push(v);
    }

    build_topo(pool, root_id, &mut visited, &mut topo);
    pool.set_grad(root_id, scalar(1.0));

    for &v in topo.iter().rev() {
        let grad = pool.get_grad(v).unwrap().clone();
        let children: Vec<ChildInfo> = pool.get(v).children.clone();

        for child in children {
            let lg_shape = child.local_grad.shape();
            let grad_shape = grad.shape();

            let child_grad = if lg_shape.is_empty() && grad_shape.is_empty() {
                let lg_val = child.local_grad[[]];
                let grad_val = grad[[]];
                scalar(lg_val * grad_val)
            } else if lg_shape.is_empty() {
                let lg_val = child.local_grad[[]];
                grad.mapv(|v| v * lg_val)
            } else if grad_shape.is_empty() {
                let grad_val = grad[[]];
                child.local_grad.mapv(|v| v * grad_val)
            } else {
                &child.local_grad * &grad
            };

            let existing = pool.take_grad(child.id);
            let new_grad = match existing {
                Some(e) => &e + &child_grad,
                None => child_grad,
            };
            pool.set_grad(child.id, new_grad);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;
    use ndarray::arr1;

    #[test]
    fn test_add_grad() {
        let mut pool = TensorPool::new();
        let a_id = pool.alloc(scalar(3.0), vec![]);
        let b_id = pool.alloc(scalar(4.0), vec![]);
        let c_id = add(a_id, b_id, &mut pool);

        backward(c_id, &mut pool);

        assert_abs_diff_eq!(pool.get(a_id).grad.as_ref().unwrap()[[]], 1.0);
        assert_abs_diff_eq!(pool.get(b_id).grad.as_ref().unwrap()[[]], 1.0);
    }

    #[test]
    fn test_mul_grad() {
        let mut pool = TensorPool::new();
        let a_id = pool.alloc(scalar(3.0), vec![]);
        let b_id = pool.alloc(scalar(4.0), vec![]);
        let c_id = mul(a_id, b_id, &mut pool);

        backward(c_id, &mut pool);

        assert_abs_diff_eq!(pool.get(a_id).grad.as_ref().unwrap()[[]], 4.0);
        assert_abs_diff_eq!(pool.get(b_id).grad.as_ref().unwrap()[[]], 3.0);
    }

    #[test]
    fn test_pow_grad() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(scalar(2.0), vec![]);
        let y_id = pow(x_id, 3.0, &mut pool);

        backward(y_id, &mut pool);

        assert_abs_diff_eq!(pool.get(y_id).data[[]], 8.0);
        assert_abs_diff_eq!(pool.get(x_id).grad.as_ref().unwrap()[[]], 12.0);
    }

    #[test]
    fn test_relu_grad() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(scalar(-2.0), vec![]);
        let y_id = relu(x_id, &mut pool);
        backward(y_id, &mut pool);
        assert_abs_diff_eq!(pool.get(y_id).data[[]], 0.0);
        assert_abs_diff_eq!(pool.get(x_id).grad.as_ref().unwrap()[[]], 0.0);
    }

    #[test]
    fn test_relu_grad_positive() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(scalar(3.0), vec![]);
        let y_id = relu(x_id, &mut pool);
        backward(y_id, &mut pool);
        assert_abs_diff_eq!(pool.get(y_id).data[[]], 3.0);
        assert_abs_diff_eq!(pool.get(x_id).grad.as_ref().unwrap()[[]], 1.0);
    }

    #[test]
    fn test_log_grad() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(scalar(2.0), vec![]);
        let y_id = log(x_id, &mut pool);
        backward(y_id, &mut pool);
        assert_abs_diff_eq!(pool.get(y_id).data[[]], 2.0_f64.ln(), epsilon = 0.001);
        assert_abs_diff_eq!(pool.get(x_id).grad.as_ref().unwrap()[[]], 0.5);
    }

    #[test]
    fn test_exp_grad() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(scalar(2.0), vec![]);
        let y_id = exp(x_id, &mut pool);
        backward(y_id, &mut pool);
        let expected = 2.0_f64.exp();
        assert_abs_diff_eq!(pool.get(y_id).data[[]], expected, epsilon = 0.001);
        assert_abs_diff_eq!(
            pool.get(x_id).grad.as_ref().unwrap()[[]],
            expected,
            epsilon = 0.001
        );
    }

    #[test]
    fn test_matmul_grad() {
        let mut pool = TensorPool::new();
        let a_id = pool.alloc(arr1(&[1.0, 2.0, 3.0, 4.0]).into_dyn(), vec![]);
        let b_id = pool.alloc(arr1(&[5.0, 6.0, 7.0, 8.0]).into_dyn(), vec![]);
        let c_id = matmul(a_id, b_id, &mut pool);
        backward(c_id, &mut pool);
        assert!(pool.get(a_id).grad.is_some());
        assert!(pool.get(b_id).grad.is_some());
    }

    #[test]
    fn test_softmax() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(arr1(&[1.0, 2.0, 3.0]).into_dyn(), vec![]);
        let y_id = softmax(x_id, &mut pool);
        let sum: f64 = pool.get(y_id).data.iter().sum();
        assert_abs_diff_eq!(sum, 1.0, epsilon = 0.001);
    }

    #[test]
    fn test_rmsnorm() {
        let mut pool = TensorPool::new();
        let x_id = pool.alloc(arr1(&[1.0, 2.0, 3.0, 4.0]).into_dyn(), vec![]);
        let y_id = rmsnorm(x_id, &mut pool);
        let ms: f64 = pool.get(y_id).data.iter().map(|v| v * v).sum::<f64>() / 4.0;
        assert_abs_diff_eq!(ms, 1.0, epsilon = 0.1);
    }

    #[test]
    fn test_adam() {
        let mut pool = TensorPool::new();
        let w_id = pool.alloc(scalar(1.0), vec![]);

        let mut optimizer = Adam::new(vec![w_id], 0.01, 0.9, 0.99, 1e-8);

        pool.set_grad(w_id, scalar(2.0));
        optimizer.step(&mut pool, None);

        assert!(pool.get(w_id).data[[]] < 1.0);
    }

    #[test]
    fn test_add_vector_scalar() {
        let mut pool = TensorPool::new();
        let vec_id = pool.alloc(arr1(&[1.0, 2.0, 3.0]).into_dyn(), vec![]);
        let scalar_id = pool.alloc(scalar(5.0), vec![]);
        let c_id = add(vec_id, scalar_id, &mut pool);

        assert_eq!(pool.get(c_id).data.shape()[0], 3);
        assert_abs_diff_eq!(pool.get(c_id).data[[0]], 6.0);
        assert_abs_diff_eq!(pool.get(c_id).data[[1]], 7.0);
        assert_abs_diff_eq!(pool.get(c_id).data[[2]], 8.0);
    }

    #[test]
    fn test_matmul_matrix_vector() {
        let mut pool = TensorPool::new();
        let a_id = pool.alloc(
            arr1(&[1.0, 0.0, 0.0, 1.0])
                .into_dyn()
                .into_shape((2, 2))
                .unwrap()
                .into_dyn(),
            vec![],
        );
        let b_id = pool.alloc(arr1(&[3.0, 4.0]).into_dyn(), vec![]);
        let c_id = matmul(a_id, b_id, &mut pool);

        assert_eq!(pool.get(c_id).data.shape()[0], 2);
        assert_abs_diff_eq!(pool.get(c_id).data[[0]], 3.0);
        assert_abs_diff_eq!(pool.get(c_id).data[[1]], 4.0);
    }

    #[test]
    fn test_linear_forward() {
        let mut pool = TensorPool::new();
        let a_id = pool.alloc(arr1(&[1.0, 2.0]).into_dyn(), vec![]);

        let w_data = arr1(&[1.0, 0.0, 0.0, 1.0])
            .into_dyn()
            .into_shape((2, 2))
            .unwrap()
            .into_dyn();
        let w_id = pool.alloc(w_data, vec![]);

        let b_id = pool.alloc(arr1(&[0.0, 0.0]).into_dyn(), vec![]);

        let wx_id = matmul(w_id, a_id, &mut pool);
        let y_id = add(wx_id, b_id, &mut pool);

        assert_eq!(pool.get(y_id).data.shape()[0], 2);
        assert_abs_diff_eq!(pool.get(y_id).data[[0]], 1.0);
        assert_abs_diff_eq!(pool.get(y_id).data[[1]], 2.0);
    }
}
