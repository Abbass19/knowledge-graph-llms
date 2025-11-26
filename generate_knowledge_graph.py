from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from pyvis.network import Network

from langchain_openai import ChatOpenAI  # LM Studio exposes an OpenAI-compatible API
import asyncio
import os

# -------------------------------
# 1. Connect to LM Studio (LOCAL)
# -------------------------------
# LM Studio must be running with:
#   - "OpenAI compatible server" enabled
#   - "localhost:1234" as the endpoint

llm = ChatOpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",     # any string works
    model="meta-llama-3.1-8b-instruct",
)

graph_transformer = LLMGraphTransformer(llm=llm)


# -------------------------------
# 2. Extract graph data
# -------------------------------
async def extract_graph_data(text):
    documents = [Document(page_content=text)]
    return await graph_transformer.aconvert_to_graph_documents(documents)


# -------------------------------
# 3. Visualize using PyVis
# -------------------------------
def visualize_graph(graph_documents):
    net = Network(
        height="1200px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=True,
        filter_menu=True,
        cdn_resources="remote"
    )

    graph = graph_documents[0]
    nodes = graph.nodes
    relationships = graph.relationships

    node_dict = {node.id: node for node in nodes}

    valid_edges = []
    valid_node_ids = set()

    for rel in relationships:
        if rel.source.id in node_dict and rel.target.id in node_dict:
            valid_edges.append(rel)
            valid_node_ids.update([rel.source.id, rel.target.id])

    for node_id in valid_node_ids:
        node = node_dict[node_id]
        net.add_node(node.id, label=node.id, title=node.type, group=node.type)

    for rel in valid_edges:
        net.add_edge(rel.source.id, rel.target.id, label=rel.type.lower())

    net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }
        }
    """)

    output_file = "knowledge_graph.html"
    net.save_graph(output_file)
    print(f"Graph saved to: {os.path.abspath(output_file)}")
    return net


# -------------------------------
# 4. Main function
# -------------------------------
def generate_knowledge_graph(text):
    graph_documents = asyncio.run(extract_graph_data(text))
    save_graph_json(graph_documents)
    return visualize_graph(graph_documents)


import json

def save_graph_json(graph_documents):
    graph = graph_documents[0]
    data = {
        "nodes": [node.dict() for node in graph.nodes],
        "relationships": [rel.dict() for rel in graph.relationships],
    }
    with open("knowledge_graph.json", "w") as f:
        json.dump(data, f, indent=4)
