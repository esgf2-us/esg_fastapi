Feature: ESG Search Request/Response parity

    The response bodies for a given request should be the same between ESG Search and ESG FastAPI

    Scenario Outline: Minimal request parameters

        Given a <query_example>
        When the request is sent to ESG FastAPI
        Then the ESG Fast API response should be the same as the ESG Search response

        Examples:
            | query_example                  |
            | 1_record_dataset_response.json |
            | 2_record_dataset_response.json |
            | 1_file_metagrid_response.json  |
            | metagrid_default_request.json  |
            | minimal_response.json          |
            | multiple_projects.json         |
            | multiple_data_nodes.json       |
