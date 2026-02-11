import json
import logging
import os
import re

import requests

from common.constants import fuTypeList

# ==================== AI Provider Configuration ====================
AI_PROVIDERS = {
    "OpenAI": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "env_key": "OPENAI_API_KEY",
        "api_type": "openai"
    },
    "Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        "env_key": "GEMINI_API_KEY",
        "api_type": "openai"  # Gemini supports OpenAI-compatible API
    },
    "Qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
        "env_key": "DASHSCOPE_API_KEY",
        "api_type": "openai"
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "env_key": "DEEPSEEK_API_KEY",
        "api_type": "openai"
    },
}

aiChatConfig = {
    "provider": "OpenAI",
    "api_key": "",
    "model": "gpt-4o-mini",
    "chat_history": [],
    "system_prompt": """You are an AI assistant for CGRA-Flow, a framework for CGRA (Coarse-Grained Reconfigurable Array) design and exploration.

## Domain Knowledge:
1. Control Units Placement: Place control FUs (Cmp, Phi, Br, Sel, Ret) preferably in central tiles for global control and reduced communication delay.
2. Balance of Compute and Memory: Each tile should ideally include at least one compute FU (Add, Mul, Logic) and one memory FU (Ld, St).
3. Vectorization and Parallelism: If the kernel has many independent operations, replicate compute units and enable vectorization.
4. Configuration Memory (configMemSize): Small kernels → fewer instructions (8-64). Complex kernels with loops/branches → larger storage (128-512).
5. Scratchpad Memory (data_spm_kb): Memory-bound kernels benefit from larger scratchpad (32-64KB). Compute-intensive kernels can use smaller (4-16KB).
6. If goal is 'high_performance': prefer larger parallelism, vectorization, higher throughput.
7. If goal is 'low_power': prefer smaller area, lower memory usage, balanced FU count.

## Available FU Types (for tile configuration):
- Compute: add, mul, div, shift, logic
- Floating-point: fadd, fmul, fdiv, fmul_fadd, fadd_fadd, vfmul
- Control: cmp, sel, phi, loop_control
- Memory: mem, mem_indexed, constant
- Other: return, grant, alloca, type_conv

IMPORTANT: By default, all FU types should be enabled in every tile whenever we design a CGRA.
The full FU list is: ["add", "mul", "div", "fadd", "fmul", "fdiv", "logic", "cmp", "sel", "type_conv", "vfmul", "fadd_fadd", "fmul_fadd", "loop_control", "phi", "constant", "mem", "mem_indexed", "shift", "return", "alloca", "grant"]

When recommending CGRA configurations, provide THREE options:

```json
{
  "high_performance": {
    "cgra_rows": <2-8>,
    "cgra_columns": <2-8>,
    "configMemSize": <8-512>,
    "data_spm_kb": <4-64>,
    "multi_cgra_rows": <1-4>,
    "multi_cgra_columns": <1-4>,
    "fu_types": ["add", "mul", "div", ...],
    "explanation": "<high_performance optimization reasoning>"
  },
  "balanced": {
    "cgra_rows": <2-8>,
    "cgra_columns": <2-8>,
    "configMemSize": <8-512>,
    "data_spm_kb": <4-64>,
    "multi_cgra_rows": <1-4>,
    "multi_cgra_columns": <1-4>,
    "fu_types": ["add", "mul", ...],
    "explanation": "<balanced trade-off reasoning>"
  },
  "low_power": {
    "cgra_rows": <2-8>,
    "cgra_columns": <2-8>,
    "configMemSize": <8-512>,
    "data_spm_kb": <4-64>,
    "multi_cgra_rows": <1-4>,
    "multi_cgra_columns": <1-4>,
    "fu_types": ["add", "mul", ...],
    "explanation": "<power saving reasoning>"
  }
}
```

Design guidelines:
- High performance: Larger array, more parallelism, larger memory, more FU types
- Balanced: Medium-sized array, good high_performance with reasonable power
- Low power: Smaller array, minimal resources, only essential FUs

Be concise. Answer in the same language as the user's question."""
}

# Store last recommended configs for applying
lastRecommendedConfigs = {
    "high_performance": {},
    "balanced": {},
    "low_power": {}
}

# Valid parameter ranges for validation
VALID_CONFIG_RANGES = {
    "cgra_rows": (2, 8),
    "cgra_columns": (2, 8),
    "configMemSize": [8, 16, 32, 64, 128, 256, 512],
    "data_spm_kb": [4, 8, 16, 32, 64],
    "multi_cgra_rows": (1, 4),
    "multi_cgra_columns": (1, 4),
}

# ==================== RAG Knowledge Base ====================
# Kernel examples with DFG characteristics and recommended configurations

ALL_FU_TYPES = [
    "add", "mul", "div",
    "fadd", "fmul", "fdiv",
    "logic", "cmp", "sel",
    "type_conv",
    "vfmul",
    "fadd_fadd", "fmul_fadd",
    "loop_control", "phi",
    "constant",
    "mem", "mem_indexed",
    "shift",
    "return", "alloca",
    "grant",
]

RAG_KERNEL_DATABASE = {
    "conv": {
        "aliases": ["convolution", "conv2d", "conv1d", "convolutional"],
        "dfg_nodes": {'Ld': 2, 'St': 0, 'Cmp': 1, 'Phi': 2, 'Br': 1, 'Sel': 0, 'Add': 4, 'Mul': 1, 'Div': 1},
        "characteristics": "compute-intensive, regular memory access, high parallelism",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled (power mainly from size/mem)"
        }
    },

    "dtw": {
        "aliases": ["dynamic time warping", "time warping"],
        "dfg_nodes": {'Ld': 4, 'St': 1, 'Cmp': 3, 'Phi': 1, 'Br': 1, 'Sel': 2, 'Add': 11, 'Mul': 0},
        "characteristics": "control-heavy, many comparisons and selections, memory-bound",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 256, "data_spm_kb": 64,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "fft": {
        "aliases": ["fast fourier transform", "fourier", "dft", "signal processing"],
        "dfg_nodes": {'Ld': 6, 'St': 4, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 11, 'Mul': 4},
        "characteristics": "memory-intensive, butterfly pattern, high memory bandwidth",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 256, "data_spm_kb": 64,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "fir": {
        "aliases": ["finite impulse response", "fir filter", "digital filter"],
        "dfg_nodes": {'Ld': 3, 'St': 1, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 4, 'Mul': 1},
        "characteristics": "regular dataflow, multiply-accumulate pattern, moderate complexity",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 16, "data_spm_kb": 4,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        }
    },

    "gemm": {
        "aliases": ["matrix multiplication", "matmul", "matrix multiply", "mm", "general matrix multiply"],
        "dfg_nodes": {'Ld': 3, 'St': 1, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 4, 'Mul': 1},
        "characteristics": "compute-intensive, regular access pattern, high data reuse",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        }
    },

    "histogram": {
        "aliases": ["hist", "histogram computation"],
        "dfg_nodes": {'Ld': 2, 'St': 1, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 5, 'Mul': 1},
        "characteristics": "irregular memory access, read-modify-write pattern",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 64, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 32, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 16, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "latnrm": {
        "aliases": ["layer normalization", "layernorm", "normalization"],
        "dfg_nodes": {'Ld': 2, 'St': 0, 'Cmp': 1, 'Phi': 2, 'Br': 1, 'Add': 5, 'Mul': 1},
        "characteristics": "reduction operation, compute mean and variance",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 32, "data_spm_kb": 4,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        }
    },

    "mvt": {
        "aliases": ["matrix vector multiply", "matvec", "mv", "vector multiply"],
        "dfg_nodes": {'Ld': 6, 'St': 2, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 7, 'Mul': 2},
        "characteristics": "memory-bound, streaming access pattern",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 64,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 64, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 32, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "relu": {
        "aliases": ["rectified linear unit", "activation", "relu activation"],
        "dfg_nodes": {'Ld': 1, 'St': 1, 'Cmp': 2, 'Phi': 1, 'Br': 1, 'Sel': 1, 'Add': 3},
        "characteristics": "simple element-wise operation, comparison-heavy",
        "high_performance": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 16, "data_spm_kb": 4,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 2, "configMemSize": 8, "data_spm_kb": 2,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x2 array with full FU set enabled"
        }
    },

    "spmv": {
        "aliases": ["sparse matrix vector", "sparse mv", "sparse multiply"],
        "dfg_nodes": {'Ld': 5, 'St': 1, 'Cmp': 1, 'Phi': 1, 'Br': 1, 'Add': 7, 'Mul': 1},
        "characteristics": "irregular memory access, indirect addressing",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 256, "data_spm_kb": 64,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x4 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 4, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x4 array with full FU set enabled"
        }
    },

    "pooling": {
        "aliases": ["max pooling", "avg pooling", "average pooling", "maxpool", "avgpool"],
        "dfg_nodes": {'Ld': 4, 'St': 1, 'Cmp': 4, 'Phi': 1, 'Br': 1, 'Sel': 2, 'Add': 2},
        "characteristics": "comparison-heavy for max, reduction for average",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 3, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x3 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 16, "data_spm_kb": 4,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "softmax": {
        "aliases": ["soft max", "attention softmax"],
        "dfg_nodes": {'Ld': 2, 'St': 1, 'Cmp': 1, 'Phi': 2, 'Br': 1, 'Add': 6, 'Mul': 2, 'Div': 1},
        "characteristics": "reduction + element-wise, needs exp/div support",
        "high_performance": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 3, "cgra_columns": 4, "configMemSize": 64, "data_spm_kb": 16,
            "fu_types": ALL_FU_TYPES,
            "explanation": "3x4 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 2, "cgra_columns": 3, "configMemSize": 32, "data_spm_kb": 8,
            "fu_types": ALL_FU_TYPES,
            "explanation": "2x3 array with full FU set enabled"
        }
    },

    "attention": {
        "aliases": ["self attention", "multi-head attention", "transformer attention"],
        "dfg_nodes": {'Ld': 6, 'St': 2, 'Cmp': 2, 'Phi': 2, 'Br': 2, 'Add': 10, 'Mul': 6, 'Div': 1},
        "characteristics": "compute-intensive, multiple matmuls, softmax",
        "high_performance": {
            "cgra_rows": 6, "cgra_columns": 6, "configMemSize": 512, "data_spm_kb": 128,
            "fu_types": ALL_FU_TYPES,
            "explanation": "6x6 array with full FU set enabled"
        },
        "balanced": {
            "cgra_rows": 5, "cgra_columns": 5, "configMemSize": 256, "data_spm_kb": 64,
            "fu_types": ALL_FU_TYPES,
            "explanation": "5x5 array with full FU set enabled"
        },
        "low_power": {
            "cgra_rows": 4, "cgra_columns": 4, "configMemSize": 128, "data_spm_kb": 32,
            "fu_types": ALL_FU_TYPES,
            "explanation": "4x4 array with full FU set enabled"
        }
    },
}



def search_rag_database(query):
    """Search RAG database for relevant kernel examples based on query."""
    query_lower = query.lower()
    matched_kernels = []

    for kernel_name, kernel_info in RAG_KERNEL_DATABASE.items():
        # Check kernel name match
        if kernel_name in query_lower:
            matched_kernels.append((kernel_name, kernel_info, 1.0))
            continue

        # Check aliases match
        for alias in kernel_info.get("aliases", []):
            if alias in query_lower:
                matched_kernels.append((kernel_name, kernel_info, 0.9))
                break

        # Check characteristics match (partial)
        chars = kernel_info.get("characteristics", "").lower()
        char_keywords = ["memory", "compute", "parallel", "regular", "irregular", "control"]
        for kw in char_keywords:
            if kw in query_lower and kw in chars:
                matched_kernels.append((kernel_name, kernel_info, 0.5))
                break

    # Remove duplicates and sort by relevance
    seen = set()
    unique_matches = []
    for item in sorted(matched_kernels, key=lambda x: -x[2]):
        if item[0] not in seen:
            seen.add(item[0])
            unique_matches.append(item)

    return unique_matches[:3]  # Return top 3 matches


def build_rag_context(query):
    """Build RAG context string from matched kernels."""
    matches = search_rag_database(query)
    if not matches:
        return ""

    context = "\n## Relevant Examples from Knowledge Base:\n"
    for kernel_name, kernel_info, score in matches:
        context += f"\n### {kernel_name.upper()}\n"
        context += f"- DFG Nodes: {kernel_info['dfg_nodes']}\n"
        context += f"- Characteristics: {kernel_info['characteristics']}\n"

        # Show all three config modes if available
        for mode_key, mode_label in [("high_performance", "High Performance"), ("balanced", "Balanced"), ("low_power", "Low Power")]:
            if mode_key in kernel_info:
                cfg = kernel_info[mode_key]
                context += f"- {mode_label}: {cfg['cgra_rows']}x{cfg['cgra_columns']}, "
                context += f"configMem={cfg['configMemSize']}, dataSPM={cfg['data_spm_kb']}KB, "
                context += f"fu_types={cfg.get('fu_types', [])}\n"

    return context


# Initialize API key from environment variable
def init_api_key_from_env():
    provider = aiChatConfig["provider"]
    env_key = AI_PROVIDERS[provider]["env_key"]
    aiChatConfig["api_key"] = os.environ.get(env_key, "")

init_api_key_from_env()


def call_openai_compatible_api(user_message, callback):
    """Call OpenAI-compatible API (OpenAI, Qwen, Gemini, DeepSeek)."""
    try:
        provider = aiChatConfig["provider"]
        api_key = aiChatConfig["api_key"]
        provider_config = AI_PROVIDERS[provider]

        if not api_key:
            env_key = provider_config["env_key"]
            callback(None, f"API Key not set.\nPlease set {env_key} environment variable\nor enter it in the API Key field.")
            return

        # Add user message to history
        aiChatConfig["chat_history"].append({
            "role": "user",
            "content": user_message
        })

        # Build RAG context if relevant
        rag_context = build_rag_context(user_message)

        # Prepare messages with system prompt (enhanced with RAG context if available)
        system_content = aiChatConfig["system_prompt"]
        if rag_context:
            system_content += rag_context

        messages = [{"role": "system", "content": system_content}]
        messages.extend(aiChatConfig["chat_history"])

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            provider_config["base_url"],
            headers=headers,
            json={
                "model": aiChatConfig["model"],
                "messages": messages
            },
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")
            aiChatConfig["chat_history"].append({
                "role": "assistant",
                "content": ai_response
            })
            callback(ai_response, None)
        else:
            try:
                error_msg = response.json().get("error", {}).get("message", f"HTTP {response.status_code}")
            except:
                error_msg = f"HTTP {response.status_code}"
            callback(None, f"API Error: {error_msg}")
    except requests.exceptions.ConnectionError:
        callback(None, "Connection failed. Please check your network.")
    except requests.exceptions.Timeout:
        callback(None, "Request timeout. Please try again.")
    except Exception as e:
        callback(None, f"Error: {str(e)}")


def call_ai_api(user_message, callback):
    """Call the appropriate AI API based on selected provider."""
    call_openai_compatible_api(user_message, callback)


def validate_and_fix_config(config):
    """Validate CGRA config and auto-fix invalid values."""
    fixed_config = {}
    fixes_made = []

    # cgra_rows validation
    rows = config.get("cgra_rows") or config.get("rows", 4)
    try:
        rows = int(rows)
    except:
        rows = 4
    min_r, max_r = VALID_CONFIG_RANGES["cgra_rows"]
    if rows < min_r:
        fixes_made.append(f"cgra_rows {rows} -> {min_r} (min)")
        rows = min_r
    elif rows > max_r:
        fixes_made.append(f"cgra_rows {rows} -> {max_r} (max)")
        rows = max_r
    fixed_config["cgra_rows"] = rows

    # cgra_columns validation
    cols = config.get("cgra_columns") or config.get("columns", 4)
    try:
        cols = int(cols)
    except:
        cols = 4
    min_c, max_c = VALID_CONFIG_RANGES["cgra_columns"]
    if cols < min_c:
        fixes_made.append(f"cgra_columns {cols} -> {min_c} (min)")
        cols = min_c
    elif cols > max_c:
        fixes_made.append(f"cgra_columns {cols} -> {max_c} (max)")
        cols = max_c
    fixed_config["cgra_columns"] = cols

    # configMemSize validation (power of 2)
    cfg_mem = config.get("configMemSize") or config.get("config_mem_size", 64)
    try:
        cfg_mem = int(cfg_mem)
    except:
        cfg_mem = 64
    valid_cfg_values = VALID_CONFIG_RANGES["configMemSize"]
    if cfg_mem not in valid_cfg_values:
        # Find nearest valid value
        nearest = min(valid_cfg_values, key=lambda x: abs(x - cfg_mem))
        fixes_made.append(f"configMemSize {cfg_mem} -> {nearest} (nearest valid)")
        cfg_mem = nearest
    fixed_config["configMemSize"] = cfg_mem

    # data_spm_kb validation (power of 2)
    data_mem = config.get("data_spm_kb") or config.get("data_mem_size", 8)
    try:
        data_mem = int(data_mem)
    except:
        data_mem = 8
    valid_mem_values = VALID_CONFIG_RANGES["data_spm_kb"]
    if data_mem not in valid_mem_values:
        nearest = min(valid_mem_values, key=lambda x: abs(x - data_mem))
        fixes_made.append(f"data_spm_kb {data_mem} -> {nearest} (nearest valid)")
        data_mem = nearest
    fixed_config["data_spm_kb"] = data_mem

    # multi_cgra_rows validation
    mc_rows = config.get("multi_cgra_rows", 1)
    try:
        mc_rows = int(mc_rows)
    except:
        mc_rows = 1
    min_mr, max_mr = VALID_CONFIG_RANGES["multi_cgra_rows"]
    if mc_rows < min_mr or mc_rows > max_mr:
        mc_rows = max(min_mr, min(mc_rows, max_mr))
        fixes_made.append(f"multi_cgra_rows -> {mc_rows}")
    fixed_config["multi_cgra_rows"] = mc_rows

    # multi_cgra_columns validation
    mc_cols = config.get("multi_cgra_columns", 1)
    try:
        mc_cols = int(mc_cols)
    except:
        mc_cols = 1
    min_mc, max_mc = VALID_CONFIG_RANGES["multi_cgra_columns"]
    if mc_cols < min_mc or mc_cols > max_mc:
        mc_cols = max(min_mc, min(mc_cols, max_mc))
        fixes_made.append(f"multi_cgra_columns -> {mc_cols}")
    fixed_config["multi_cgra_columns"] = mc_cols

    # fu_types validation
    fu_types = config.get("fu_types", [])
    if fu_types and isinstance(fu_types, list):
        valid_fus = []
        for fu in fu_types:
            if fu in fuTypeList:
                valid_fus.append(fu)
            else:
                fixes_made.append(f"Removed invalid FU: {fu}")
        fixed_config["fu_types"] = valid_fus
    else:
        fixed_config["fu_types"] = []

    # Keep explanation
    fixed_config["explanation"] = config.get("explanation", "")

    return fixed_config, fixes_made


def extract_cgra_config(ai_response):
    """Extract CGRA configuration from AI response if present."""
    global lastRecommendedConfigs
    try:
        # Find JSON block in response
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
        if json_match:
            config_str = json_match.group(1)
            config = json.loads(config_str)

            found = False
            # Check for tri-mode config (high_performance + balanced + low_power)
            if "high_performance" in config:
                raw_perf = config["high_performance"]
                fixed_perf, fixes = validate_and_fix_config(raw_perf)
                lastRecommendedConfigs["high_performance"] = fixed_perf
                if fixes:
                    logging.info(f"High performance config auto-fixed: {fixes}")
                found = True

            if "balanced" in config:
                raw_bal = config["balanced"]
                fixed_bal, fixes = validate_and_fix_config(raw_bal)
                lastRecommendedConfigs["balanced"] = fixed_bal
                if fixes:
                    logging.info(f"Balanced config auto-fixed: {fixes}")
                found = True

            if "low_power" in config:
                raw_lp = config["low_power"]
                fixed_lp, fixes = validate_and_fix_config(raw_lp)
                lastRecommendedConfigs["low_power"] = fixed_lp
                if fixes:
                    logging.info(f"Low power config auto-fixed: {fixes}")
                found = True

            # Fallback: old single cgra_config format
            if not found and "cgra_config" in config:
                raw_config = config["cgra_config"]
                fixed_config, fixes = validate_and_fix_config(raw_config)
                lastRecommendedConfigs["high_performance"] = fixed_config
                lastRecommendedConfigs["balanced"] = fixed_config
                lastRecommendedConfigs["low_power"] = fixed_config
                if fixes:
                    logging.info(f"Config auto-fixed: {fixes}")
                found = True

            if found:
                logging.info(f"Extracted configs: perf={lastRecommendedConfigs['high_performance']}, bal={lastRecommendedConfigs['balanced']}, lp={lastRecommendedConfigs['low_power']}")
                return True
    except Exception as e:
        logging.warning(f"Failed to extract CGRA config: {e}")
    return False
