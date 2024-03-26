Feature: ESG Search Request/Response parity

    The response bodies for a given request should be the same between ESG Search and ESG FastAPI

    Scenario Outline: Minimal request parameters

        Given a <query_example>
        When the request is sent to ESG FastAPI
        Then the ESG Fast API response should be the same as the ESG Search response

        Examples:
            | query_example         |
            | minimal_response.json |
