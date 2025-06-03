import json
from typing import List, Dict, Any
from langchain_core.documents import Document
import json

def create_embedding_text_from_features(product_data: Dict[str, Any],
                                        feature_list: List[str],
                                        label_map: Dict[str, str]) -> str:
    """
    Creates a concatenated text string for a single product,
    using a specific list of features and their labels.
    """
    text_parts = []
    for feature_key in feature_list:
        value = product_data.get(feature_key)
        label = label_map.get(feature_key, feature_key.replace('_', ' ').title())
        
        if value is not None:
            if isinstance(value, (list, tuple)):
                value_str = ", ".join(str(v) for v in value)
            elif isinstance(value, (int, float)):
                value_str = str(value)
            else:
                value_str = str(value).strip()
                
            if value_str:
                text_parts.append(f"{label}: {value_str}.")
                
    concatenated_text = " ".join(text_parts)
    return concatenated_text.replace("\n", " ").replace("  ", " ")

def prepare_product_documents(raw_product_list: List[Dict[str, Any]],
                              feature_list: List[str],
                              label_map: Dict[str, str]) -> List[Document]:
    """
    Process raw product data into LangChain Document objects for vector embedding.
    """
    lc_documents = []
    for product_raw in raw_product_list:
        if not product_raw or not product_raw.get("id"):
            continue
            
        page_content = create_embedding_text_from_features(product_raw, feature_list, label_map)
        metadata = {
            "product_id": str(product_raw.get("id")),
            "name": product_raw.get("name"),
            "price": product_raw.get("price"),
            "document_type": "product",
            "original_data_json_str": json.dumps(product_raw)
        }
        
        lc_documents.append(Document(page_content=page_content, metadata=metadata))
        
    print(f"Prepared {len(lc_documents)} product documents.")
    return lc_documents

def prepare_skin_condition_documents(skin_conditions: Dict[str, str]) -> List[Document]:
    """
    Process skin condition profiles into LangChain Document objects for vector embedding.
    """
    lc_documents = []
    
    for condition_name, description in skin_conditions.items():
        # Clean up the description text
        clean_description = description.replace("\n", " ").replace("  ", " ").strip()
        
        metadata = {
            "condition_name": condition_name,
            "document_type": "skin_condition"
        }
        
        lc_documents.append(Document(page_content=clean_description, metadata=metadata))
        
    print(f"Prepared {len(lc_documents)} skin condition documents.")
    return lc_documents
