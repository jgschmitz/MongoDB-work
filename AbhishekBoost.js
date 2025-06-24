# for anyone!
{
  "$search": {
    "index": "autocomplete_parsed_text",
    "compound": {
      "should": [
        {
          "text": {
            "query": "event",
            "path": "doc_text",
            "score": {
              "boost": {
                "value": 2
              }
            }
          }
        },
        {
          "autocomplete": {
            "query": "event",
            "path": "doc_text",
            "score": {
              "boost": {
                "value": 1
              }
            }
          }
        },
        {
          "embeddedDocument": {
            "path": "document_metadata",
            "operator": {
              "compound": {
                "should": [
                  {
                    "autocomplete": {
                      "path": "document_metadata.search_tags",
                      "query": "event"
                    }
                  },
                  {
                    "text": {
                      "path": "document_metadata.doc_title",
                      "query": "event"
                    }
                  }
                ]
              }
            },
            "score": {
              "embedded": {
                "aggregate": "sum"
              }
            }
          }
        }
      ],
      "minimumShouldMatch": 1,
      "filter": [
        {
          "equals": {
            "path": "doc_version",
            "value": 1
          }
        },
        {
          "embeddedDocument": {
            "path": "document_metadata",
            "operator": {
              "compound": {
                "must": [
                  {
                    "text": {
                      "path": "document_metadata.published_by",
                      "query": "vpriya@paloaltonetworks.com"
                    }
                  },
                  {
                    "embeddedDocument": {
                      "path": "document_metadata.approval_details",
                      "operator": {
                        "compound": {
                          "must": [
                            {
                              "text": {
                                "query": "john.doe@example.com",
                                "path": "document_metadata.approval_details.approver_email"
                              }
                            }
                          ]
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        }
      ]
    }
  }
}
