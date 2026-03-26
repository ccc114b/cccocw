use rand::Rng;
use rand::seq::SliceRandom;

fn rand_normal(rng: &mut impl Rng) -> f64 {
    let u1: f64 = rng.gen();
    let u2: f64 = rng.gen();
    let u1 = if u1 == 0.0 { 1e-10 } else { u1 };
    (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
}

const N_LAYER: usize = 1;
const N_EMBD: usize = 16;
const BLOCK_SIZE: usize = 16;
const N_HEAD: usize = 4;
const HEAD_DIM: usize = N_EMBD / N_HEAD;
const NUM_STEPS: usize = 1000;

#[derive(Clone)]
struct Value {
    data: f64,
    grad: f64,
    children: Vec<(usize, f64)>,
}

struct ValuePool {
    values: Vec<Value>,
}

impl ValuePool {
    fn new() -> Self {
        Self { values: Vec::new() }
    }

    fn alloc(&mut self, data: f64, children: Vec<(usize, f64)>) -> usize {
        let handle = self.values.len();
        self.values.push(Value { data, grad: 0.0, children });
        handle
    }

    fn get(&self, handle: usize) -> &Value {
        &self.values[handle]
    }

    fn get_mut(&mut self, handle: usize) -> &mut Value {
        &mut self.values[handle]
    }

    fn len(&self) -> usize {
        self.values.len()
    }
}

fn add(a: f64, b: f64, children: Vec<(usize, f64)>, pool: &mut ValuePool) -> usize {
    pool.alloc(a + b, children)
}

fn mul(a: f64, b: f64, ca: f64, cb: f64, pool: &mut ValuePool) -> usize {
    pool.alloc(a * b, vec![(0, ca), (0, cb)])
}

fn neg(a: f64, pool: &mut ValuePool) -> usize {
    pool.alloc(-a, vec![])
}

fn sub(a_handle: usize, b_handle: usize, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let b = pool.get(b_handle).data;
    pool.alloc(a - b, vec![(a_handle, 1.0), (b_handle, -1.0)])
}

fn div(a_handle: usize, b_handle: usize, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let b = pool.get(b_handle).data;
    let a_over_b = a / b;
    let b_sq = b * b;
    pool.alloc(a_over_b, vec![(a_handle, 1.0/b), (b_handle, -a/b_sq)])
}

fn scalarmul(a_handle: usize, s: f64, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    pool.alloc(a * s, vec![(a_handle, s)])
}

fn pow(a_handle: usize, exp: f64, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let result = a.powf(exp);
    let da = exp * a.powf(exp - 1.0);
    pool.alloc(result, vec![(a_handle, da)])
}

fn log(a_handle: usize, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let result = a.ln();
    let da = 1.0 / a;
    pool.alloc(result, vec![(a_handle, da)])
}

fn exp(a_handle: usize, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let result = a.exp();
    pool.alloc(result, vec![(a_handle, result)])
}

fn relu(a_handle: usize, pool: &mut ValuePool) -> usize {
    let a = pool.get(a_handle).data;
    let result = a.max(0.0);
    let da = if a > 0.0 { 1.0 } else { 0.0 };
    pool.alloc(result, vec![(a_handle, da)])
}

fn backward(pool: &mut ValuePool, root: usize) {
    let n = pool.len();
    let mut topo: Vec<usize> = Vec::new();
    let mut visited = vec![false; n];

    fn build_topo(pool: &ValuePool, v: usize, visited: &mut Vec<bool>, topo: &mut Vec<usize>) {
        if visited[v] { return; }
        visited[v] = true;
        for (child, _) in &pool.get(v).children {
            build_topo(pool, *child, visited, topo);
        }
        topo.push(v);
    }

    build_topo(pool, root, &mut visited, &mut topo);

    pool.get_mut(root).grad = 1.0;

    for &v in topo.iter().rev() {
        let children = pool.get(v).children.clone();
        let grad = pool.get(v).grad;
        for (child, local_grad) in children {
            pool.get_mut(child).grad += local_grad * grad;
        }
    }
}

struct Linear {
    w: Vec<Vec<usize>>,
}

impl Linear {
    fn new(pool: &mut ValuePool, nout: usize, nin: usize, std: f64) -> Self {
    let mut rng = rand::thread_rng();
        let mut w = Vec::with_capacity(nout);
        for _ in 0..nout {
            let mut row = Vec::with_capacity(nin);
            for _ in 0..nin {
                let v = pool.alloc(rand_normal(&mut rng) * std, vec![]);
                row.push(v);
            }
            w.push(row);
        }
        Self { w }
    }

    fn forward(&self, pool: &mut ValuePool, x: &[usize]) -> Vec<usize> {
        self.w.iter().map(|wo| {
            let mut sum_handle = wo[0];
            for (wi, xi) in wo.iter().zip(x.iter()).skip(1) {
                let a = pool.get(sum_handle).data;
                let b = pool.get(*wi).data * pool.get(*xi).data;
                sum_handle = pool.alloc(a + b, vec![(sum_handle, 1.0), (*wi, pool.get(*xi).data), (*xi, pool.get(*wi).data)]);
            }
            sum_handle
        }).collect()
    }
}

fn rmsnorm_forward(x: &[usize], pool: &mut ValuePool) -> Vec<usize> {
    let nin = x.len();
    let mut sum_sq_handle = pool.alloc(0.0, vec![]);
    for &xi in x {
        let a = pool.get(sum_sq_handle).data;
        let b = pool.get(xi).data * pool.get(xi).data;
        sum_sq_handle = pool.alloc(a + b, vec![(sum_sq_handle, 1.0), (xi, 2.0 * pool.get(xi).data)]);
    }
    let ms_handle = scalarmul(sum_sq_handle, 1.0 / nin as f64, pool);
    let eps_handle = pool.alloc(1e-5, vec![]);
    let ms_eps_handle = pool.alloc(pool.get(ms_handle).data + pool.get(eps_handle).data, vec![(ms_handle, 1.0), (eps_handle, 1.0)]);
    let inv_sqrt = pow(ms_eps_handle, -0.5, pool);
    x.iter().map(|&xi| {
        let a = pool.get(xi).data;
        let b = pool.get(inv_sqrt).data;
        pool.alloc(a * b, vec![(xi, b), (inv_sqrt, a)])
    }).collect()
}

struct Layer {
    attn_wq: Linear,
    attn_wk: Linear,
    attn_wv: Linear,
    attn_wo: Linear,
    mlp_fc1: Linear,
    mlp_fc2: Linear,
}

impl Layer {
    fn new(pool: &mut ValuePool) -> Self {
        Self {
            attn_wq: Linear::new(pool, N_EMBD, N_EMBD, 0.08),
            attn_wk: Linear::new(pool, N_EMBD, N_EMBD, 0.08),
            attn_wv: Linear::new(pool, N_EMBD, N_EMBD, 0.08),
            attn_wo: Linear::new(pool, N_EMBD, N_EMBD, 0.08),
            mlp_fc1: Linear::new(pool, 4 * N_EMBD, N_EMBD, 0.08),
            mlp_fc2: Linear::new(pool, N_EMBD, 4 * N_EMBD, 0.08),
        }
    }

    fn forward(
        &self,
        pool: &mut ValuePool,
        x: &[usize],
        keys: &mut [Vec<Vec<usize>>],
        values: &mut [Vec<Vec<usize>>],
        layer_idx: usize,
    ) -> Vec<usize> {
        let x_residual: Vec<usize> = x.to_vec();
        let x_norm = rmsnorm_forward(x, pool);
        
        let q = self.attn_wq.forward(pool, &x_norm);
        let k = self.attn_wk.forward(pool, &x_norm);
        let v = self.attn_wv.forward(pool, &x_norm);
        
        keys[layer_idx].push(k.clone());
        values[layer_idx].push(v.clone());
        
        let mut x_attn = Vec::with_capacity(N_EMBD);
        for h in 0..N_HEAD {
            let hs = h * HEAD_DIM;
            let q_h: Vec<usize> = q[hs..hs+HEAD_DIM].to_vec();
            let k_h: Vec<Vec<usize>> = keys[layer_idx].iter().map(|k| k[hs..hs+HEAD_DIM].to_vec()).collect();
            let v_h: Vec<Vec<usize>> = values[layer_idx].iter().map(|v| v[hs..hs+HEAD_DIM].to_vec()).collect();
            
            let mut attn_logits = Vec::new();
            for t in 0..k_h.len() {
                let mut sum_handle = pool.alloc(0.0, vec![]);
                for j in 0..HEAD_DIM {
                    let a = pool.get(sum_handle).data;
                    let b = pool.get(q_h[j]).data * pool.get(k_h[t][j]).data;
                    sum_handle = pool.alloc(a + b, vec![(sum_handle, 1.0), (q_h[j], pool.get(k_h[t][j]).data), (k_h[t][j], pool.get(q_h[j]).data)]);
                }
                let scale = (HEAD_DIM as f64).sqrt().recip();
                let a = pool.get(sum_handle).data;
                sum_handle = pool.alloc(a * scale, vec![(sum_handle, scale)]);
                attn_logits.push(sum_handle);
            }
            
            let max_val = attn_logits.iter().map(|l| pool.get(*l).data).fold(f64::NEG_INFINITY, f64::max);
            let max_handles: Vec<usize> = attn_logits.iter().map(|l| {
                sub(*l, pool.alloc(max_val, vec![]), pool)
            }).collect();
            let exps: Vec<usize> = max_handles.iter().map(|l| exp(*l, pool)).collect();
            
            let mut total_handle = pool.alloc(0.0, vec![]);
            for e in &exps {
                let a = pool.get(total_handle).data;
                let b = pool.get(*e).data;
                total_handle = pool.alloc(a + b, vec![(total_handle, 1.0), (*e, 1.0)]);
            }
            
            let probs: Vec<usize> = exps.iter().map(|e| div(*e, total_handle, pool)).collect();
            
            let mut head_out = Vec::new();
            for j in 0..HEAD_DIM {
                let mut sum_handle = pool.alloc(0.0, vec![]);
                for (t, &prob) in probs.iter().enumerate() {
                    let a = pool.get(sum_handle).data;
                    let b = pool.get(prob).data * pool.get(v_h[t][j]).data;
                    sum_handle = pool.alloc(a + b, vec![(sum_handle, 1.0), (prob, pool.get(v_h[t][j]).data), (v_h[t][j], pool.get(prob).data)]);
                }
                head_out.push(sum_handle);
            }
            x_attn.extend(head_out);
        }
        
        let x_attn = self.attn_wo.forward(pool, &x_attn);
        let x: Vec<usize> = x_residual.iter().zip(x_attn.iter()).map(|(&a, &b)| {
            let a_data = pool.get(a).data;
            let b_data = pool.get(b).data;
            pool.alloc(a_data + b_data, vec![(a, 1.0), (b, 1.0)])
        }).collect();
        
        let x_residual2: Vec<usize> = x.to_vec();
        let x_norm2 = rmsnorm_forward(&x, pool);
        let x_fc = self.mlp_fc1.forward(pool, &x_norm2);
        let x_act: Vec<usize> = x_fc.iter().map(|&v| relu(v, pool)).collect();
        let x_fc2 = self.mlp_fc2.forward(pool, &x_act);
        let x: Vec<usize> = x_residual2.iter().zip(x_fc2.iter()).map(|(&a, &b)| {
            let a_data = pool.get(a).data;
            let b_data = pool.get(b).data;
            pool.alloc(a_data + b_data, vec![(a, 1.0), (b, 1.0)])
        }).collect();
        
        x
    }
}

struct GPT {
    wte: Linear,
    wpe: Linear,
    lm_head: Linear,
    layers: Vec<Layer>,
}

impl GPT {
    fn new(pool: &mut ValuePool, vocab_size: usize) -> Self {
        let mut layers = Vec::new();
        for _ in 0..N_LAYER {
            layers.push(Layer::new(pool));
        }
        Self {
            wte: Linear::new(pool, vocab_size, N_EMBD, 0.08),
            wpe: Linear::new(pool, BLOCK_SIZE, N_EMBD, 0.08),
            lm_head: Linear::new(pool, vocab_size, N_EMBD, 0.08),
            layers,
        }
    }

    fn forward(
        &self,
        pool: &mut ValuePool,
        token_id: usize,
        pos_id: usize,
        keys: &mut [Vec<Vec<usize>>],
        values: &mut [Vec<Vec<usize>>],
    ) -> Vec<usize> {
        let tok_emb = &self.wte.w[token_id];
        let pos_emb = &self.wpe.w[pos_id];
        
        let mut x: Vec<usize> = tok_emb.iter().zip(pos_emb.iter()).map(|(&t, &p)| {
            let t_data = pool.get(t).data;
            let p_data = pool.get(p).data;
            pool.alloc(t_data + p_data, vec![(t, 1.0), (p, 1.0)])
        }).collect();
        
        x = rmsnorm_forward(&x, pool);
        
        for (i, layer) in self.layers.iter().enumerate() {
            x = layer.forward(pool, &x, keys, values, i);
        }
        
        self.lm_head.forward(pool, &x)
    }
}

fn main() {
    let mut pool = ValuePool::new();
    
    let docs: Vec<String> = std::fs::read_to_string("input.txt")
        .unwrap_or_else(|_| {
            let names = vec![
                "alice", "bob", "charlie", "david", "eve", "frank", "grace", "henry",
                "ivy", "jack", "kate", "leo", "mary", "nancy", "oliver", "peter",
            ];
            std::fs::write("input.txt", names.join("\n")).unwrap();
            std::fs::read_to_string("input.txt").unwrap()
        })
        .lines()
        .map(|s| s.to_string())
        .filter(|s| !s.is_empty())
        .collect();
    
    let mut rng = rand::thread_rng();
    let mut docs: Vec<String> = docs;
    docs.shuffle(&mut rng);
    println!("num docs: {}", docs.len());
    
    let mut uchars: Vec<char> = docs.join("").chars().collect();
    uchars.sort();
    uchars.dedup();
    let vocab_size = uchars.len() + 1;
    let bos = uchars.len();
    println!("vocab size: {}", vocab_size);
    
    let mut gpt = GPT::new(&mut pool, vocab_size);
    
    let mut param_count = 0;
    param_count += gpt.wte.w.iter().map(|r| r.len()).sum::<usize>();
    param_count += gpt.wpe.w.iter().map(|r| r.len()).sum::<usize>();
    param_count += gpt.lm_head.w.iter().map(|r| r.len()).sum::<usize>();
    for layer in &gpt.layers {
        param_count += layer.attn_wq.w.iter().map(|r| r.len()).sum::<usize>();
        param_count += layer.attn_wk.w.iter().map(|r| r.len()).sum::<usize>();
        param_count += layer.attn_wv.w.iter().map(|r| r.len()).sum::<usize>();
        param_count += layer.attn_wo.w.iter().map(|r| r.len()).sum::<usize>();
        param_count += layer.mlp_fc1.w.iter().map(|r| r.len()).sum::<usize>();
        param_count += layer.mlp_fc2.w.iter().map(|r| r.len()).sum::<usize>();
    }
    println!("num params: {}", param_count);
    
    let mut param_handles: Vec<usize> = Vec::new();
    for row in &gpt.wte.w { param_handles.extend(row); }
    for row in &gpt.wpe.w { param_handles.extend(row); }
    for row in &gpt.lm_head.w { param_handles.extend(row); }
    for layer in &gpt.layers {
        for row in &layer.attn_wq.w { param_handles.extend(row); }
        for row in &layer.attn_wk.w { param_handles.extend(row); }
        for row in &layer.attn_wv.w { param_handles.extend(row); }
        for row in &layer.attn_wo.w { param_handles.extend(row); }
        for row in &layer.mlp_fc1.w { param_handles.extend(row); }
        for row in &layer.mlp_fc2.w { param_handles.extend(row); }
    }
    
    let mut m = vec![0.0; param_handles.len()];
    let mut v = vec![0.0; param_handles.len()];
    let learning_rate = 0.01;
    let beta1 = 0.85;
    let beta2 = 0.99;
    let eps_adam = 1e-8;
    
    for step in 0..NUM_STEPS {
        let doc = &docs[step % docs.len()];
        let tokens: Vec<usize> = std::iter::once(bos)
            .chain(doc.chars().map(|c| uchars.iter().position(|&x| x == c).unwrap()))
            .chain(std::iter::once(bos))
            .collect();
        
        let n = BLOCK_SIZE.min(tokens.len() - 1);
        
        let mut keys: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
        let mut values: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
        
        let mut loss_sum_handle = pool.alloc(0.0, vec![]);
        
        for pos_id in 0..n {
            let token_id = tokens[pos_id];
            let target_id = tokens[pos_id + 1];
            
            let mut local_keys: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
            let mut local_values: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
            
            let logits = gpt.forward(&mut pool, token_id, pos_id, &mut local_keys, &mut local_values);
            
            let max_logit = logits.iter().map(|l| pool.get(*l).data).fold(f64::NEG_INFINITY, f64::max);
            let shifted: Vec<usize> = logits.iter().map(|l| sub(*l, pool.alloc(max_logit, vec![]), &mut pool)).collect();
            let exps: Vec<usize> = shifted.iter().map(|l| exp(*l, &mut pool)).collect();
            
            let mut total_handle = pool.alloc(0.0, vec![]);
            for e in &exps {
                let a = pool.get(total_handle).data;
                let b = pool.get(*e).data;
                total_handle = pool.alloc(a + b, vec![(total_handle, 1.0), (*e, 1.0)]);
            }
            
            let probs: Vec<usize> = exps.iter().map(|e| div(*e, total_handle, &mut pool)).collect();
            
            let loss_t = log(probs[target_id], &mut pool);
            let neg_loss = scalarmul(loss_t, -1.0, &mut pool);
            
            let a = pool.get(loss_sum_handle).data;
            let b = pool.get(neg_loss).data;
            loss_sum_handle = pool.alloc(a + b, vec![(loss_sum_handle, 1.0), (neg_loss, 1.0)]);
        }
        
        let n_handle = pool.alloc(n as f64, vec![]);
        let loss = div(loss_sum_handle, n_handle, &mut pool);
        
        backward(&mut pool, loss);
        
        let lr_t = learning_rate * (1.0 - step as f64 / NUM_STEPS as f64);
        
        for (i, &p) in param_handles.iter().enumerate() {
            let grad = pool.get(p).grad;
            m[i] = beta1 * m[i] + (1.0 - beta1) * grad;
            v[i] = beta2 * v[i] + (1.0 - beta2) * grad * grad;
            let m_hat = m[i] / (1.0 - beta1.powi(step as i32 + 1));
            let v_hat = v[i] / (1.0 - beta2.powi(step as i32 + 1));
            let update = lr_t * m_hat / (v_hat.sqrt() + eps_adam);
            pool.get_mut(p).data -= update;
            pool.get_mut(p).grad = 0.0;
        }
        
        print!("step {:4} / {:4} | loss {:.4}\r", step + 1, NUM_STEPS, pool.get(loss).data);
    }
    
    println!("\n--- inference (new, hallucinated names) ---");
    let temperature = 1.5;
    
    for sample_idx in 0..20 {
        let mut keys: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
        let mut values: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
        let mut token_id = bos;
        let mut sample = String::new();
        
        for _ in 0..BLOCK_SIZE {
            let mut local_keys: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
            let mut local_values: Vec<Vec<Vec<usize>>> = vec![vec![]; N_LAYER];
            
            let pos_id = sample.len().min(BLOCK_SIZE - 1);
            let logits = gpt.forward(&mut pool, token_id, pos_id, &mut local_keys, &mut local_values);
            
            let scaled: Vec<usize> = logits.iter().map(|l| scalarmul(*l, 1.0 / temperature, &mut pool)).collect();
            let max_logit = scaled.iter().map(|l| pool.get(*l).data).fold(f64::NEG_INFINITY, f64::max);
            let shifted: Vec<usize> = scaled.iter().map(|l| sub(*l, pool.alloc(max_logit, vec![]), &mut pool)).collect();
            let exps: Vec<usize> = shifted.iter().map(|l| exp(*l, &mut pool)).collect();
            
            let mut total_handle = pool.alloc(0.0, vec![]);
            for e in &exps {
                let a = pool.get(total_handle).data;
                let b = pool.get(*e).data;
                total_handle = pool.alloc(a + b, vec![(total_handle, 1.0), (*e, 1.0)]);
            }
            let probs: Vec<usize> = exps.iter().map(|e| div(*e, total_handle, &mut pool)).collect();
            
            let mut weights: Vec<(usize, f64)> = probs.iter().enumerate()
                .map(|(i, p)| (i, pool.get(*p).data))
                .collect();
            weights.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
            let top_k = 5;
            let top_weights: Vec<f64> = weights.iter().take(top_k).map(|(_, w)| *w).collect();
            let top_indices: Vec<usize> = weights.iter().take(top_k).map(|(i, _)| *i).collect();
            
            let sum: f64 = top_weights.iter().sum();
            let r: f64 = rng.gen::<f64>() * sum;
            let mut cum = 0.0;
            let mut new_token_id = 0;
            for (i, &w) in top_weights.iter().enumerate() {
                cum += w;
                if r <= cum {
                    new_token_id = top_indices[i];
                    break;
                }
            }
            if new_token_id == bos {
                break;
            }
            token_id = new_token_id;
            
            sample.push(uchars[token_id]);
        }
        
        println!("sample {:2}: {}", sample_idx + 1, sample);
    }
}