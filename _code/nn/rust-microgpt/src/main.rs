use rand::distributions::WeightedIndex;
use rand::seq::SliceRandom;
use rand::{thread_rng, Rng};
use rand_distr::StandardNormal;
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::process::Command;
use std::rc::Rc;

// -----------------------------------------------------------------------------
// 1. Autograd 引擎 (使用 Rc<RefCell<>> 來管理動態計算圖)
// -----------------------------------------------------------------------------

struct ValueInner {
    data: f64,
    grad: f64,
    children: Vec<Value>,
    local_grads: Vec<f64>,
}

#[derive(Clone)]
struct Value(Rc<RefCell<ValueInner>>);

impl Value {
    fn new(data: f64) -> Self {
        Value(Rc::new(RefCell::new(ValueInner {
            data,
            grad: 0.0,
            children: vec![],
            local_grads: vec![],
        })))
    }

    fn with_children(data: f64, children: Vec<Value>, local_grads: Vec<f64>) -> Self {
        Value(Rc::new(RefCell::new(ValueInner {
            data,
            grad: 0.0,
            children,
            local_grads,
        })))
    }

    fn data(&self) -> f64 {
        self.0.borrow().data
    }

    fn set_data(&self, val: f64) {
        self.0.borrow_mut().data = val;
    }

    fn grad(&self) -> f64 {
        self.0.borrow().grad
    }

    fn add_grad(&self, val: f64) {
        self.0.borrow_mut().grad += val;
    }

    fn set_grad(&self, val: f64) {
        self.0.borrow_mut().grad = val;
    }

    // Math operations
    fn add(&self, other: &Value) -> Value {
        Value::with_children(self.data() + other.data(), vec![self.clone(), other.clone()], vec![1.0, 1.0])
    }

    fn mul(&self, other: &Value) -> Value {
        Value::with_children(
            self.data() * other.data(),
            vec![self.clone(), other.clone()],
            vec![other.data(), self.data()],
        )
    }

    fn pow(&self, other: f64) -> Value {
        Value::with_children(
            self.data().powf(other),
            vec![self.clone()],
            vec![other * self.data().powf(other - 1.0)],
        )
    }

    fn log(&self) -> Value {
        Value::with_children(self.data().ln(), vec![self.clone()], vec![1.0 / self.data()])
    }

    fn exp(&self) -> Value {
        let val = self.data().exp();
        Value::with_children(val, vec![self.clone()], vec![val])
    }

    fn relu(&self) -> Value {
        let out = self.data().max(0.0);
        let grad = if self.data() > 0.0 { 1.0 } else { 0.0 };
        Value::with_children(out, vec![self.clone()], vec![grad])
    }

    fn neg(&self) -> Value {
        self.mul(&Value::new(-1.0))
    }

    fn sub(&self, other: &Value) -> Value {
        self.add(&other.neg())
    }

    fn div(&self, other: &Value) -> Value {
        self.mul(&other.pow(-1.0))
    }

    // 計算反向傳播
    fn backward(&self) {
        let mut topo = Vec::new();
        let mut visited = HashSet::new();

        fn build_topo(v: &Value, visited: &mut HashSet<*const ValueInner>, topo: &mut Vec<Value>) {
            let ptr = Rc::as_ptr(&v.0);
            if !visited.contains(&ptr) {
                visited.insert(ptr);
                for child in &v.0.borrow().children {
                    build_topo(child, visited, topo);
                }
                topo.push(v.clone());
            }
        }

        build_topo(self, &mut visited, &mut topo);

        self.set_grad(1.0);
        for v in topo.into_iter().rev() {
            let grad = v.grad();
            let inner = v.0.borrow();
            for (child, local_grad) in inner.children.iter().zip(inner.local_grads.iter()) {
                child.add_grad(local_grad * grad);
            }
        }
    }
}

// -----------------------------------------------------------------------------
// 2. 工具函數：建立矩陣與神經網路區塊
// -----------------------------------------------------------------------------

fn matrix(nout: usize, nin: usize, std: f64) -> Vec<Vec<Value>> {
    let mut rng = thread_rng();
    (0..nout)
        .map(|_| {
            (0..nin)
                .map(|_| {
                    let val: f64 = rng.sample(StandardNormal);
                    Value::new(val * std)
                })
                .collect()
        })
        .collect()
}

fn linear(x: &[Value], w: &[Vec<Value>]) -> Vec<Value> {
    w.iter()
        .map(|wo| {
            let mut sum = Value::new(0.0);
            for (wi, xi) in wo.iter().zip(x.iter()) {
                sum = sum.add(&wi.mul(xi));
            }
            sum
        })
        .collect()
}

fn softmax(logits: &[Value]) -> Vec<Value> {
    let max_val = logits.iter().map(|v| v.data()).fold(f64::NEG_INFINITY, f64::max);
    let max_v = Value::new(max_val);
    let exps: Vec<Value> = logits.iter().map(|v| v.sub(&max_v).exp()).collect();
    let mut total = Value::new(0.0);
    for e in &exps {
        total = total.add(e);
    }
    exps.iter().map(|e| e.div(&total)).collect()
}

fn rmsnorm(x: &[Value]) -> Vec<Value> {
    let n = x.len() as f64;
    let mut ms = Value::new(0.0);
    for xi in x {
        ms = ms.add(&xi.mul(xi));
    }
    ms = ms.mul(&Value::new(1.0 / n));
    
    // scale = (ms + 1e-5) ** -0.5
    let scale = ms.add(&Value::new(1e-5)).pow(-0.5);
    x.iter().map(|xi| xi.mul(&scale)).collect()
}

// -----------------------------------------------------------------------------
// 3. 主程式
// -----------------------------------------------------------------------------

fn main() {
    // 確保有資料集
    if !std::path::Path::new("input.txt").exists() {
        println!("Downloading dataset...");
        Command::new("curl")
            .args(["-o", "input.txt", "https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt"])
            .status()
            .expect("Failed to download dataset");
    }

    let file_content = fs::read_to_string("input.txt").unwrap();
    let mut docs: Vec<String> = file_content.lines()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    let mut rng = thread_rng();
    docs.shuffle(&mut rng);
    println!("num docs: {}", docs.len());

    let mut char_set: Vec<char> = file_content.chars().filter(|c| !c.is_whitespace() || *c == ' ').collect();
    char_set.sort();
    char_set.dedup();
    let mut uchars: Vec<char> = char_set.into_iter().filter(|c| c.is_ascii_alphabetic()).collect();
    
    let bos_token = uchars.len();
    let vocab_size = uchars.len() + 1;
    println!("vocab size: {}", vocab_size);

    // Initialize the parameters
    let n_layer = 1;
    let n_embd = 16;
    let block_size = 16;
    let n_head = 4;
    let head_dim = n_embd / n_head;

    let mut state_dict: HashMap<String, Vec<Vec<Value>>> = HashMap::new();
    state_dict.insert("wte".to_string(), matrix(vocab_size, n_embd, 0.08));
    state_dict.insert("wpe".to_string(), matrix(block_size, n_embd, 0.08));
    state_dict.insert("lm_head".to_string(), matrix(vocab_size, n_embd, 0.08));

    for i in 0..n_layer {
        state_dict.insert(format!("layer{}.attn_wq", i), matrix(n_embd, n_embd, 0.08));
        state_dict.insert(format!("layer{}.attn_wk", i), matrix(n_embd, n_embd, 0.08));
        state_dict.insert(format!("layer{}.attn_wv", i), matrix(n_embd, n_embd, 0.08));
        state_dict.insert(format!("layer{}.attn_wo", i), matrix(n_embd, n_embd, 0.08));
        state_dict.insert(format!("layer{}.mlp_fc1", i), matrix(4 * n_embd, n_embd, 0.08));
        state_dict.insert(format!("layer{}.mlp_fc2", i), matrix(n_embd, 4 * n_embd, 0.08));
    }

    let mut params: Vec<Value> = Vec::new();
    for mat in state_dict.values() {
        for row in mat {
            for p in row {
                params.push(p.clone());
            }
        }
    }
    println!("num params: {}", params.len());

    // GPT Model
    let gpt = |token_id: usize, pos_id: usize, keys: &mut Vec<Vec<Vec<Value>>>, values: &mut Vec<Vec<Vec<Value>>>| -> Vec<Value> {
        let tok_emb = &state_dict["wte"][token_id];
        let pos_emb = &state_dict["wpe"][pos_id];
        
        let mut x: Vec<Value> = tok_emb.iter().zip(pos_emb.iter()).map(|(t, p)| t.add(p)).collect();
        x = rmsnorm(&x);

        for li in 0..n_layer {
            // 1) Multi-head Attention
            let x_residual = x.clone();
            x = rmsnorm(&x);
            let q = linear(&x, &state_dict[&format!("layer{}.attn_wq", li)]);
            let k = linear(&x, &state_dict[&format!("layer{}.attn_wk", li)]);
            let v = linear(&x, &state_dict[&format!("layer{}.attn_wv", li)]);
            
            keys[li].push(k);
            values[li].push(v);
            
            let mut x_attn = Vec::new();
            for h in 0..n_head {
                let hs = h * head_dim;
                let q_h = &q[hs..hs+head_dim];
                let k_h: Vec<Vec<Value>> = keys[li].iter().map(|ki| ki[hs..hs+head_dim].to_vec()).collect();
                let v_h: Vec<Vec<Value>> = values[li].iter().map(|vi| vi[hs..hs+head_dim].to_vec()).collect();
                
                let mut attn_logits = Vec::new();
                let scale = (head_dim as f64).powf(0.5);
                for t in 0..k_h.len() {
                    let mut score = Value::new(0.0);
                    for j in 0..head_dim {
                        score = score.add(&q_h[j].mul(&k_h[t][j]));
                    }
                    attn_logits.push(score.mul(&Value::new(1.0 / scale)));
                }
                
                let attn_weights = softmax(&attn_logits);
                let mut head_out = Vec::new();
                for j in 0..head_dim {
                    let mut val = Value::new(0.0);
                    for t in 0..v_h.len() {
                        val = val.add(&attn_weights[t].mul(&v_h[t][j]));
                    }
                    head_out.push(val);
                }
                x_attn.extend(head_out);
            }
            x = linear(&x_attn, &state_dict[&format!("layer{}.attn_wo", li)]);
            x = x.into_iter().zip(x_residual.into_iter()).map(|(a, b)| a.add(&b)).collect();
            
            // 2) MLP block
            let x_residual = x.clone();
            x = rmsnorm(&x);
            x = linear(&x, &state_dict[&format!("layer{}.mlp_fc1", li)]);
            x = x.into_iter().map(|xi| xi.relu()).collect();
            x = linear(&x, &state_dict[&format!("layer{}.mlp_fc2", li)]);
            x = x.into_iter().zip(x_residual.into_iter()).map(|(a, b)| a.add(&b)).collect();
        }
        
        linear(&x, &state_dict["lm_head"])
    };

    // Adam Optimizer
    let learning_rate = 0.01;
    let beta1 = 0.85;
    let beta2 = 0.99;
    let eps_adam = 1e-8;
    let mut m = vec![0.0; params.len()];
    let mut v = vec![0.0; params.len()];

    let num_steps = 1000;
    for step in 0..num_steps {
        let doc = &docs[step % docs.len()];
        let mut tokens = vec![bos_token];
        for ch in doc.chars() {
            if let Some(pos) = uchars.iter().position(|&x| x == ch) {
                tokens.push(pos);
            }
        }
        tokens.push(bos_token);
        let n = usize::min(block_size, tokens.len().saturating_sub(1));

        let mut keys: Vec<Vec<Vec<Value>>> = vec![vec![]; n_layer];
        let mut values: Vec<Vec<Vec<Value>>> = vec![vec![]; n_layer];
        let mut losses = Vec::new();

        for pos_id in 0..n {
            let token_id = tokens[pos_id];
            let target_id = tokens[pos_id + 1];
            
            let logits = gpt(token_id, pos_id, &mut keys, &mut values);
            let probs = softmax(&logits);
            let loss_t = probs[target_id].log().neg();
            losses.push(loss_t);
        }

        let mut total_loss = Value::new(0.0);
        for l in &losses {
            total_loss = total_loss.add(l);
        }
        let loss = total_loss.mul(&Value::new(1.0 / n as f64));

        // Backward
        loss.backward();

        // Adam Update
        let lr_t = learning_rate * (1.0 - (step as f64) / (num_steps as f64));
        for i in 0..params.len() {
            let p = &params[i];
            let grad = p.grad();
            
            m[i] = beta1 * m[i] + (1.0 - beta1) * grad;
            v[i] = beta2 * v[i] + (1.0 - beta2) * grad.powi(2);
            
            let m_hat = m[i] / (1.0 - beta1.powi((step + 1) as i32));
            let v_hat = v[i] / (1.0 - beta2.powi((step + 1) as i32));
            
            let current_data = p.data();
            p.set_data(current_data - lr_t * m_hat / (v_hat.sqrt() + eps_adam));
            p.set_grad(0.0);
        }

        print!("step {:4} / {:4} | loss {:.4}\r", step + 1, num_steps, loss.data());
        use std::io::Write;
        std::io::stdout().flush().unwrap();
    }

    // Inference
    let temperature = 0.5;
    println!("\n--- inference (new, hallucinated names) ---");
    for sample_idx in 0..20 {
        let mut keys: Vec<Vec<Vec<Value>>> = vec![vec![]; n_layer];
        let mut values: Vec<Vec<Vec<Value>>> = vec![vec![]; n_layer];
        let mut token_id = bos_token;
        let mut sample = String::new();

        for pos_id in 0..block_size {
            let logits = gpt(token_id, pos_id, &mut keys, &mut values);
            
            let scaled_logits: Vec<Value> = logits.iter().map(|l| l.mul(&Value::new(1.0 / temperature))).collect();
            let probs = softmax(&scaled_logits);
            
            let weights: Vec<f64> = probs.iter().map(|p| p.data()).collect();
            let dist = WeightedIndex::new(&weights).unwrap();
            token_id = rng.sample(dist);

            if token_id == bos_token {
                break;
            }
            sample.push(uchars[token_id]);
        }
        println!("sample {:2}: {}", sample_idx + 1, sample);
    }
}