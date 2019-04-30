This application search data in play store by scrapping and matching the input name.It also gives detail result of if provided particular application application id.It saves details result in postgres database.It also cache details data if hitted by user more then once.

##requiremets to run this app

    --install and run postgres in your machine
    --install and run redis server in your machine
    --all other requirements will get install by requirements.txt


##Usage

    $$ To see home page hit -  http://127.0.0.1:8000/scrap
    $$ To search in play store hit url -  http://127.0.0.1:8000/search?app_name=<any key word by which you want to search>
    $$ To get detail of particular app hit url -  http://127.0.0.1:8000/detail?app_id<id of application>

##How search works
    -In Search api i search the key word in play store and return the required result

##How detail works
    -In detail api if the ap id is not present in database or redis if scrap it from play store and store in postgres database and also in redis if hitted same time.

  