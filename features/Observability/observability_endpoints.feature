Feature: The API provides observability endpoints for use by Kubernetes

    Kubernetes expects pods to provide a method to query their liveness (running or not)
    and readiness (whether its ready to serve traffic) states.

    Scenario Outline: Happy path (live and ready)

        Given a <probe_type>
        When its <endpoint> is querried
        Then it should return a positive <status>

        Examples:
            | probe_type | endpoint           | status |
            | readiness  | /healthz/readiness | ready  |
            | liveness   | /healthz/liveness  | live   |
