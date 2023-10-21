{
    "$search": {
        "knnBeta": {
            "vector": vector_query,
            "path": "embedding",
            "k": K * 10,
            "filter": {
                "compound": {
                    "must": [
                        {
                            "or": {
                                "values": category_list,
                                "path": "metadata.category"
                            }
                        }
                    ]
                }
            }
        }
    }
} 
