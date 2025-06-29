Feature: Traces should propagate throughout the system.

    Traces provided by the client should be expanded, provided to upstream services,
    and returned to the client.

    Scenario Outline: Traces provided by the client

        Given the client provides a trace header
        When a request is sent upstream
        And a response is returned to the client
        Then upstream requests should include the same trace header
        And the response should include the same trace header