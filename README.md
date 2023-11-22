# ruby0database

ruby0database is a simple tool to access some ICON Ruby0 namelist and easy
parameter data.
The main product is a dash web application which can be found here:
https://ruby0database.onrender.com

ruby0database is maintained here:
https://gitlab.dkrz.de/m300602/ruby0database

## Maintenance via Github:

Render.com settings can be changed here: https://dashboard.render.com/web/srv-clet9c6f27hc73bgabo0

### Update procedure:

* commit changes
* push to github `git push github master`
* on render.com choose: `Manual Deplay` and `Deploy latest commit`

## Outdated maintenance on HEROKU:

ruby0database has moved from HEROKU to render.com

See Heroku logs:

```
heroku logs --tail
```

### Derive database data

To derive the database data use `pp/pp_derive_ruby0_database.py`

### Heroku deployment steps

!!! Does not work from Mistral, do from local computer.

Information for Heroku deployment taken from here: https://dash.plotly.com/deployment

If new python packages were installed do first:

```
pip freeze > requirements.txt
```

Update heroku:

```
git status # view the changes
git add .  # add all the changes
git commit -m 'a description of the changes'
git push heroku master
```
