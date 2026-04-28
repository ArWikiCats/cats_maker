okay, after refactor `new_api` into `api2`

I found that: WikiApiClient is used

but not:

-   Transport
-   AuthProvider

also:

functions in both `super_login.py` and `auth.py`:

-   `def log_in`
-   `def _get_logintoken`
-   `def _get_login_result`
-   `def _logged_in`
-   `def _make_new_r3_token`
-   `def ensure_logged_in`

functions in both `super_login.py` and `transport.py`:

-   `def _raw_request`

functions in both `super_login.py` and `client.py`:

-   `def filter_params`
-   `def p_url`
-   `def make_response`
-   `def post_params`
-   `def post_it_parse_data`
-   `def _make_new_r3_token`

Write plan

-   to merge functions between WikiApiClient/Login
-   to use Transport and AuthProvider
-   then:
    -   to merge functions between Transport/Login
    -   to merge functions between AuthProvider/Login
