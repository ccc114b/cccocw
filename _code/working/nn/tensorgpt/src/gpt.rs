use crate::nn::{GPTBlock, Linear};
use crate::tensor::{
    add, backward, matmul, scalar, softmax as tensor_softmax, zeros, Adam, TensorPool,
};
use rand::Rng;

pub struct GPT {
    pub wte: Linear,
    pub wpe: Linear,
    pub lm_head: Linear,
    pub blocks: Vec<GPTBlock>,
    pub n_embd: usize,
    pub n_layer: usize,
    pub n_head: usize,
    pub block_size: usize,
    pub vocab_size: usize,
}

impl GPT {
    pub fn new(
        vocab_size: usize,
        n_embd: usize,
        n_layer: usize,
        n_head: usize,
        block_size: usize,
        pool: &mut TensorPool,
    ) -> Self {
        let wte = Linear::new(n_embd, vocab_size, pool);
        let wpe = Linear::new(n_embd, block_size, pool);
        let lm_head = Linear::new(n_embd, vocab_size, pool);

        let mut blocks = Vec::new();
        for _ in 0..n_layer {
            blocks.push(GPTBlock::new(n_embd, n_head, pool));
        }

        Self {
            wte,
            wpe,
            lm_head,
            blocks,
            n_embd,
            n_layer,
            n_head,
            block_size,
            vocab_size,
        }
    }

    pub fn forward(
        &self,
        token_id: usize,
        pos_id: usize,
        keys: &mut Vec<Vec<usize>>,
        values: &mut Vec<Vec<usize>>,
        pool: &mut TensorPool,
    ) -> usize {
        eprintln!("DEBUG forward: token_id={}, pos_id={}", token_id, pos_id);

        let tok_emb = self.get_embedding(token_id, &self.wte, pool);
        let tok_emb_shape = pool.get(tok_emb).data.shape();
        eprintln!("DEBUG forward: tok_emb shape={:?}", tok_emb_shape);

        let pos_emb = self.get_embedding(pos_id, &self.wpe, pool);
        let pos_emb_shape = pool.get(pos_emb).data.shape();
        eprintln!("DEBUG forward: pos_emb shape={:?}", pos_emb_shape);

        let x_id = add(tok_emb, pos_emb, pool);
        eprintln!(
            "DEBUG forward: x_id={}, x shape={:?}",
            x_id,
            pool.get(x_id).data.shape()
        );

        for (layer_idx, block) in self.blocks.iter().enumerate() {
            keys.push(Vec::new());
            values.push(Vec::new());
            eprintln!(
                "DEBUG forward: calling block.forward for layer {}",
                layer_idx
            );
            let _ = block.forward(x_id, keys, values, layer_idx, pool);
            eprintln!("DEBUG forward: block.forward returned");
        }

        let logits = self.lm_head.forward(x_id, pool);
        logits
    }

    fn get_embedding(&self, id: usize, linear: &Linear, pool: &mut TensorPool) -> usize {
        let w_data = &pool.get(linear.w_id).data;
        let nout = w_data.shape()[0];
        let nin = w_data.shape()[1];

        if id >= nout {
            panic!("id {} >= nout {}", id, nout);
        }

        let mut emb_vec = Vec::with_capacity(nin);
        for j in 0..nin {
            emb_vec.push(w_data[[id, j]]);
        }

        let emb_data = ndarray::arr1(&emb_vec).into_dyn();
        pool.alloc(emb_data, vec![])
    }

    pub fn params(&self) -> Vec<usize> {
        let mut p = self.wte.params();
        p.extend(self.wpe.params());
        p.extend(self.lm_head.params());
        for block in &self.blocks {
            p.extend(block.params());
        }
        p
    }
}

pub fn train(
    model: &GPT,
    optimizer: &mut Adam,
    docs: &[String],
    uchars: &[char],
    BOS: usize,
    pool: &mut TensorPool,
    num_steps: usize,
) {
    println!("Training for {} steps ...", num_steps);

    for step in 0..num_steps {
        let doc = &docs[step % docs.len()];
        let tokens: Vec<usize> = std::iter::once(BOS)
            .chain(
                doc.chars()
                    .map(|ch| uchars.iter().position(|&c| c == ch).unwrap_or(0)),
            )
            .chain(std::iter::once(BOS))
            .collect();

        let n = std::cmp::min(model.block_size, tokens.len() - 1);

        let mut keys: Vec<Vec<usize>> = vec![Vec::new(); model.n_layer];
        let mut values: Vec<Vec<usize>> = vec![Vec::new(); model.n_layer];

        let mut loss_sum = 0.0;

        for pos_id in 0..n {
            let token_id = tokens[pos_id];
            let target_id = tokens[pos_id + 1];

            eprintln!(
                "DEBUG train: pos_id={}, token_id={}, target_id={}",
                pos_id, token_id, target_id
            );

            let logits_id = model.forward(token_id, pos_id, &mut keys, &mut values, pool);

            let logits_shape = pool.get(logits_id).data.shape();
            if logits_shape.len() != 1 {
                eprintln!("DEBUG: logits_id={}, shape={:?}", logits_id, logits_shape);
                panic!("logits should be 1D, got shape {:?}", logits_shape);
            }

            let max_val = pool
                .get(logits_id)
                .data
                .iter()
                .fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            let vocab_size = model.vocab_size;

            let mut sum_exp = 0.0;
            for i in 0..vocab_size {
                sum_exp += (pool.get(logits_id).data[[i]] - max_val).exp();
            }
            let loss = sum_exp.ln() - (pool.get(logits_id).data[[target_id]] - max_val);
            loss_sum += loss;

            let loss_id = pool.alloc(scalar(loss), vec![]);
            backward(loss_id, pool);
        }

        let avg_loss = loss_sum / n as f64;

        let lr = optimizer.lr * (1.0 - step as f64 / num_steps as f64);
        optimizer.step(pool, Some(lr));

        if step % 100 == 0 {
            println!("step {} / {} | loss {:.4}", step, num_steps, avg_loss);
        }
    }
}

pub fn inference(
    model: &GPT,
    uchars: &[char],
    BOS: usize,
    pool: &mut TensorPool,
    num_samples: usize,
    temperature: f64,
) {
    println!(
        "--- inference ({} samples, temperature={}) ---",
        num_samples, temperature
    );
    let vocab_size = model.vocab_size;

    for _ in 0..num_samples {
        let mut keys: Vec<Vec<usize>> = vec![Vec::new(); model.n_layer];
        let mut values: Vec<Vec<usize>> = vec![Vec::new(); model.n_layer];
        let mut token_id = BOS;
        let mut sample_chars = Vec::new();

        for pos_id in 0..model.block_size {
            let logits_id = model.forward(token_id, pos_id, &mut keys, &mut values, pool);

            let mut logits: Vec<f64> = (0..vocab_size)
                .map(|i| pool.get(logits_id).data[[i]] / temperature)
                .collect();

            let max_val = logits
                .iter()
                .cloned()
                .fold(f64::NEG_INFINITY, |a, b| a.max(b));
            let sum_exp: f64 = logits.iter().map(|v| (v - max_val).exp()).sum();
            let probs: Vec<f64> = logits
                .iter()
                .map(|v| (v - max_val).exp() / sum_exp)
                .collect();

            let mut rng = rand::thread_rng();
            let r: f64 = rng.gen();
            let mut cumsum = 0.0;
            token_id = 0;
            for (i, &p) in probs.iter().enumerate() {
                cumsum += p;
                if r <= cumsum {
                    token_id = i;
                    break;
                }
            }

            if token_id == BOS {
                break;
            }

            if let Some(&ch) = uchars.get(token_id) {
                sample_chars.push(ch);
            }
        }

        println!("sample: {}", sample_chars.iter().collect::<String>());
    }
}
