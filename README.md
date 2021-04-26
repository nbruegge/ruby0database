# ruby0database

ruby0database is a simple tool to access some ICON Ruby0 namelist and easy
parameter data.
The main product is a dash web application which can be found here:
https://ruby0overview.herokuapp.com/

ruby0database is maintained here:
https://gitlab.dkrz.de/m300602/ruby0database

## Maintenance:

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
