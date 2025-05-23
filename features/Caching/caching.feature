Feature: The API caches responses from Globus Search to reduce load and conserve resources

    The `Cache-Control` header provides an http standard to cooperatively control
    caching mechanisms

    Scenario Outline: Etag

        Given that the client provides an <if-none-match> etag
        When the result for that etag is cached
        Then it should return status code <HTTP_304_NOT_MODIFIED>

        Given that the client provides an <if-match> etag
        When the result for that etag is cached
        And the cache_key does not match the provided etag
        Then it should return status code <HTTP_412_PRECONDITION_FAILED>

    Scenario Outline: Response Directives

        Given that all ESGF data is public
        When the API sends a response
        Then the <public> cache control directive should be set

        Given that publication syncronization only runs every 5 minutes
        When the API sends a response
        Then the <max-age> directive should be set to <300> seconds

        Given that users can still make use of stale results
        When the API sends a response
        Then the <stale-while-revalidate> directive should be set to <300> seconds

        Given that users can still make use of stale results
        When the API sends a response
        Then the <stale-if-error> directive should be set to <300> seconds

    Scenario Outline: Server side Caching

        Given that publication syncronization only runs every 5 minutes
        When the API sends a response
        Then the Globus Search response should be added to the local cache

        Given that the client sends a query
        When the Globus Search response is already in the cache
        Then the server should not query Globus Search again