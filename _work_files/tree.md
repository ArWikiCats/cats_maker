```
src/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── cats_helpers/
│   │   ├── __init__.py
│   │   ├── ar_from_en2.py
│   │   ├── cat_tools2.py
│   │   └── sub_cats_bot.py
│   ├── new_c18/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── category_generator.py
│   │   │   ├── category_resolver.py
│   │   │   ├── category_validator.py
│   │   │   ├── cross_wiki_linker.py
│   │   │   └── member_lister.py
│   │   ├── io/
│   │   │   ├── __init__.py
│   │   │   ├── json_store.py
│   │   │   └── sql_queries.py
│   │   ├── models.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── doc_handler.py
│   │   │   ├── sort.py
│   │   │   └── template_query.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text.py
│   └── utils/
│       ├── __init__.py
│       └── skip_cats.py
├── db/
│   ├── __init__.py
│   └── analytics/
│       ├── __init__.py
│       ├── client.py
│       ├── maps.py
│       └── replica_db.py
├── logger_config.py
├── mk_cats/
│   ├── __init__.py
│   ├── add_bot.py
│   ├── categorytext.py
│   ├── categorytext_data.py
│   ├── create_category_page.py
│   ├── members_helper.py
│   ├── mknew.py
│   └── utils/
│       ├── __init__.py
│       ├── check_en.py
│       ├── filter_en.py
│       ├── New_Portal_List.json
│       └── portal_list.py
├── shared/
│   ├── __init__.py
│   ├── api_page/
│   │   └── __init__.py
│   ├── api_sql/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── lcn_new.py
│   ├── newapi/
│   │   ├── __init__.py
│   │   ├── api_client/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── cookies_client.py
│   │   │   ├── exceptions.py
│   │   │   └── requests_handler.py
│   │   ├── client_wiki/
│   │   │   ├── __init__.py
│   │   │   ├── all_apis.py
│   │   │   ├── api_utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ask_bot.py
│   │   │   │   ├── bot_edit/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── bot_edit_by_templates.py
│   │   │   │   │   └── bot_edit_by_time.py
│   │   │   │   ├── handel_errors.py
│   │   │   │   └── txtlib.py
│   │   │   ├── bot_api.py
│   │   │   ├── categories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── catdepth_new.py
│   │   │   │   └── category_db.py
│   │   │   ├── constants.py
│   │   │   └── pages/
│   │   │       ├── __init__.py
│   │   │       ├── data.py
│   │   │       └── super_page.py
│   │   ├── core/
│   │   │   └── exceptions.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── functions_timer.py
│   └── wd_api/
│       ├── __init__.py
│       ├── to_wd.py
│       ├── wd_api_bot.py
│       └── wd_bots_main.py
└── temp/
    ├── __init__.py
    └── bots/
        ├── __init__.py
        ├── load_data.py
        ├── new.py
        ├── temp_cent.py
        ├── temp_decades.py
        ├── temp_elff.py
        └── temp_years.py

```