```
tests/
├── conftest.py
├── integration/
│   ├── __init__.py
│   └── test_main_flow.py
└── unit/
    ├── config/
    │   ├── __init__.py
    │   └── test_settings.py
    ├── core/
    │   ├── cats_helpers/
    │   │   ├── test_ar_from_en2.py
    │   │   ├── test_cat_tools2.py
    │   │   └── test_sub_cats_bot.py
    │   ├── new_c18/
    │   │   ├── __init__.py
    │   │   ├── core/
    │   │   │   ├── test_category_generator.py
    │   │   │   ├── test_category_resolver.py
    │   │   │   ├── test_category_validator.py
    │   │   │   ├── test_cross_wiki_linker.py
    │   │   │   └── test_member_lister.py
    │   │   ├── io/
    │   │   │   ├── test_json_store.py
    │   │   │   └── test_sql_queries.py
    │   │   ├── test_cat_tools_enlist2.py
    │   │   ├── test_constants.py
    │   │   ├── test_models.py
    │   │   ├── tools/
    │   │   │   ├── test_doc_handler.py
    │   │   │   ├── test_sort.py
    │   │   │   └── test_template_query.py
    │   │   └── utils/
    │   │       └── test_text.py
    │   ├── utils/
    │   │   ├── __init__.py
    │   │   └── test_skip_cats.py
    │   └── wiki_api/
    │       └── __init__.py
    ├── mk_cats/
    │   ├── __init__.py
    │   ├── mk_bots/
    │   │   ├── __init__.py
    │   │   └── test_filter_en.py
    │   ├── test_add_bot.py
    │   ├── test_categorytext.py
    │   ├── test_categorytext_data.py
    │   ├── test_create_category_page.py
    │   ├── test_members_helper.py
    │   ├── test_mknew.py
    │   └── utils/
    │       ├── __init__.py
    │       ├── test_check_en.py
    │       ├── test_filter_en.py
    │       └── test_portal_list.py
    ├── shared/
    │   ├── api_sql/
    │   │   ├── __init__.py
    │   │   ├── test_constants.py
    │   │   ├── test_exceptions.py
    │   │   ├── test_repository.py
    │   │   ├── test_service.py
    │   │   ├── test_utils.py
    │   │   └── test_wiki_sql.py
    │   ├── newapi/
    │   │   ├── api_client/
    │   │   │   ├── test_client.py
    │   │   │   ├── test_cookies_client.py
    │   │   │   ├── test_exceptions.py
    │   │   │   └── test_requests_handler.py
    │   │   └── client_wiki/
    │   │       ├── api_utils/
    │   │       │   ├── test_ask_bot.py
    │   │       │   └── test_handel_errors.py
    │   │       ├── categories/
    │   │       │   ├── test_catdepth_new.py
    │   │       │   └── test_category_db.py
    │   │       ├── pages/
    │   │       │   └── test_super_page.py
    │   │       ├── test_all_apis.py
    │   │       ├── test_constants.py
    │   │       └── test_factory.py
    │   ├── test_LCN_new.py
    │   └── wd_api/
    │       ├── __init__.py
    │       ├── test_handle_wd_errors.py
    │       ├── test_to_wd.py
    │       ├── test_wd_api_bot.py
    │       └── test_wd_bots_main.py
    └── temp/
        ├── _test_temp_more.py
        ├── bots/
        │   ├── test_load_data.py
        │   ├── test_new.py
        │   ├── test_temp_cent.py
        │   ├── test_temp_decades.py
        │   ├── test_temp_elff.py
        │   └── test_temp_years.py
        ├── test_temp.py
        └── test_temp_more_data.py

```