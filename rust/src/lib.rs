use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use regex::Regex;
use serde::Deserialize;
use serde_json::{Map, Value};
use std::collections::HashSet;
use unicode_normalization::{char::is_combining_mark, UnicodeNormalization};

#[derive(Deserialize)]
struct Line {
    text: String,
    #[serde(rename = "box")]
    bx: [f64; 4],
}

/// Sans accents, en minuscules.
fn norm(s: &str) -> String {
    s.nfd().filter(|c| !is_combining_mark(*c)).collect::<String>().to_lowercase()
}

fn str_list(spec: &Value, key: &str) -> Vec<String> {
    spec[key]
        .as_array()
        .map(|a| a.iter().filter_map(|v| v.as_str().map(norm)).collect())
        .unwrap_or_default()
}

/// Applique fix_digits / pattern / format de la config a un texte brut.
fn extract(spec: &Value, text: &str, re: Option<&Regex>) -> String {
    let mut text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if spec["fix_digits"].as_bool().unwrap_or(false) {
        text = text.replace(['O', 'o'], "0");
    }
    let Some(re) = re else { return text };
    let Some(caps) = re.captures(&text) else { return text };
    let m = if caps.len() > 1 { caps.get(1) } else { caps.get(0) };
    let found = m.map(|m| m.as_str()).unwrap_or("").to_string();
    match spec["format"].as_str() {
        Some(fmt) => fmt.replace("{}", &found),
        None => found,
    }
}

fn run(lines_json: &str, config_json: &str) -> Result<String, String> {
    let lines: Vec<Line> = serde_json::from_str(lines_json).map_err(|e| e.to_string())?;
    let config: Value = serde_json::from_str(config_json).map_err(|e| e.to_string())?;
    let x_tol = config["x_tol"].as_f64().unwrap_or(2.0);
    let max_gap = config["max_gap"].as_f64().unwrap_or(3.0);
    let fields = config["fields"].as_object().ok_or("config: 'fields' manquant")?;
    let norm_texts: Vec<String> = lines.iter().map(|l| norm(&l.text)).collect();

    // libelle de chaque champ = premiere ligne contenant un de ses mots-cles
    let mut labels: Vec<(&String, Option<usize>)> = Vec::new();
    for (field, spec) in fields {
        let kws = str_list(spec, "labels");
        let idx = norm_texts.iter().position(|t| kws.iter().any(|k| t.contains(k.as_str())));
        labels.push((field, idx));
    }
    let label_ids: HashSet<usize> = labels.iter().filter_map(|(_, i)| *i).collect();

    let mut out = Map::new();
    for (field, label_idx) in labels {
        let spec = &fields[field];
        let re = match spec["pattern"].as_str() {
            Some(p) => Some(Regex::new(p).map_err(|e| format!("{field}: {e}"))?),
            None => None,
        };
        let mut value = String::new();

        if let Some(li) = label_idx {
            let [x1, y1, _, y2] = lines[li].bx;
            let h = y2 - y1;
            // valeur = ligne la plus proche sous le libelle, alignee a gauche sur lui
            let best = lines
                .iter()
                .enumerate()
                .filter(|(i, v)| {
                    !label_ids.contains(i)
                        && (v.bx[0] - x1).abs() <= x_tol * h
                        && v.bx[1] - y2 >= 0.0
                        && v.bx[1] - y2 <= max_gap * h
                })
                .min_by(|a, b| a.1.bx[1].total_cmp(&b.1.bx[1]));
            if let Some((_, v)) = best {
                value = extract(spec, &v.text, re.as_ref());
            }
        }
        if value.is_empty() && spec["search_all"].as_bool().unwrap_or(false) {
            if let Some(re) = &re {
                // repli : champ au format reconnaissable
                if let Some(l) = lines.iter().find(|l| re.is_match(&l.text)) {
                    value = extract(spec, &l.text, Some(re));
                }
            }
        }
        out.insert(field.clone(), Value::String(value));
    }
    serde_json::to_string(&out).map_err(|e| e.to_string())
}

/// parse(lines_json, config_json) -> json des champs
#[pyfunction]
fn parse(lines_json: &str, config_json: &str) -> PyResult<String> {
    run(lines_json, config_json).map_err(PyValueError::new_err)
}

#[pymodule]
fn docparse(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse, m)?)
}
