#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from os import abort
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, abort, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mypassword@localhost:5432/fyyurapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime,nullable=False)
    venue = db.relationship('Venue')
    artist = db.relationship('Artist')
    venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id', ondelete='CASCADE'),nullable=False)
    artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id', ondelete='CASCADE'),nullable=False )

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show')
    venue = db.relationship('Venue', secondary='shows',
      backref=db.backref('artist', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []

  areas = Venue.query.with_entities(Venue.city,Venue.state).group_by(Venue.city,Venue.state).all()

  for area in areas:
        venue_data = []
        venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
        for venue in venues:
              no__of_upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
              venue_data.append({
                  'id': venue.id,
                  'name': venue.name,
                  'num_upcoming_shows': len(no__of_upcoming_shows)
              })

        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form['search_term']
  search_val = "%{}%".format(search_term)

  venues = Venue.query.with_entities(Venue.id, Venue.name).filter(Venue.name.ilike(search_val)).all()

  venues_data = []
  for venue in venues:
      no_of_upcoming_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
      venues_data.append({
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': len(no_of_upcoming_shows)
      })

  response = {
      'venues': venues_data,
      'count': len(venues)
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue_data = Venue.query.filter(Venue.id == venue_id).first()

  no_of_upcoming_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

  if len(no_of_upcoming_shows) > 0:
      dupcoming_shows = []

      for upcoming_show in no_of_upcoming_shows:
          artist = Artist.query.filter(Artist.id == upcoming_show.artist_id).first()
          dupcoming_shows.append({
              'artist_id': artist.id,
              'artist_name': artist.name,
              'artist_image_link': artist.image_link,
              'start_time': str(upcoming_show.start_time),
          })

      venue_data.upcoming_shows = dupcoming_shows
      venue_data.upcoming_shows_count = len(dupcoming_shows)

  past_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

  if len(past_shows) > 0:
      past_shows_data = []
      for past_show in past_shows:
          artist = Artist.query.filter(Artist.id == past_show.artist_id).first()
          past_shows_data.append({
              'artist_id': artist.id,
              'artist_name': artist.name,
              'artist_image_link': artist.image_link,
              'start_time': str(past_show.start_time),
          })

      venue_data.past_shows = past_shows_data
      venue_data.past_shows_count = len(past_shows_data)
  
  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm()

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  phone = request.form['phone']
  image_link = request.form['image_link']
  facebook_link = request.form['facebook_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  if request.form['seeking_talent']:
        seeking_talent = True
  else:
        seeking_talent = False
  seeking_description = request.form['seeking_description']

  try:
      venue = Venue(
        name=name,
        city=city,
        state=state,
        address=address,
        phone=phone,
        image_link=image_link,
        facebook_link=facebook_link,
        genres=genres,
        website=website,
        seeking_talent=seeking_talent,
        seeking_description=seeking_description,
      )

      db.session.add(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      abort(400)
  else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  error = False

  try:
      Venue.query.filter_by(id=venue_id).delete()
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash(
        'Error: Deletion did not happen!'
      )  
      abort(400)
  else:
      flash(
        'Venue successful deletion!'
      )

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artist_data = Artist.query.order_by('id').all()

  for artist in artist_data:
      no_of_upcoming_shows = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).count()
      data.append({
          'id': artist.id,
          'name': artist.name,
          'num_upcoming_shows': no_of_upcoming_shows
      })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form['search_term']
  search = "%{}%".format(search_term)

  artist_data = Artist.query.filter(Artist.name.ilike(search)).all()

  data = []
  for artist in artist_data:
      no_of_upcoming_shows = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).count()
      data.append({
          'id': artist.id,
          'name': artist.name,
          'num_upcoming_shows': no_of_upcoming_shows
      })

  response = {
      'data': data,
      'count': len(artists)
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  artist_data = Artist.query.filter(Artist.id == artist_id).first()

  no_of_upcoming_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
  if len(no_of_upcoming_shows) > 0:
      dupcoming_shows = []

      for upcoming_show in no_of_upcoming_shows:
          venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()
          dupcoming_shows.append({
              'venue_id': venue.id,
              'venue_name': venue.name,
              'venue_image_link': venue.image_link,
              'start_time': str(upcoming_show.start_time),
          })

      artist_data.upcoming_shows = dupcoming_shows
      artist_data.upcoming_shows_count = len(dupcoming_shows)

  past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
  if len(past_shows) > 0:
      past_shows_data = []
      for past_show in past_shows:
          venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()
          past_shows_data.append({
              'venue_id': venue.id,
              'venue_name': venue.name,
              'venue_image_link': venue.image_link,
              'start_time': str(past_show.start_time),
          })

      artist_data.past_shows = past_shows_data
      artist_data.past_shows_count = len(past_shows_data)
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist_data = Artist.query.filter(Artist.id == artist_id).first()

  form = ArtistForm()
  form.name.data = artist_data.name
  form.city.data = artist_data.city
  form.state.data = artist_data.state
  form.phone.data = artist_data.phone
  form.image_link.data = artist_data.image_link
  form.facebook_link.data = artist_data.facebook_link
  form.genres.data = artist_data.genres
  form.website.data = artist_data.website
  form.seeking_venue.data = artist_data.seeking_venue
  form.seeking_description.data = artist_data.seeking_description
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  image_link = request.form['image_link']
  facebook_link = request.form['facebook_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  if request.form['seeking_venue']:
        seeking_venue = True 
  else:
        seeking_venue = False
  seeking_description = request.form['seeking_description']

  try:
      artist = Artist.query.get(artist_id)
      artist.name = name
      artist.city = city
      artist.state = state
      artist.phone = phone
      artist.image_link = image_link
      artist.facebook_link = facebook_link
      artist.website = website
      artist.genres = genres
      artist.seeking_venue = seeking_venue
      artist.seeking_description = seeking_description

      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash(
      'Error: Artist could not be updated'
      )
      abort(400)
  else:
      flash(
        'Artist updation succesful!'
      )

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).first()

  form = VenueForm()
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.website.data = venue.website
  form.genres.data = venue.genres
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  phone = request.form['phone']
  image_link = request.form['image_link']
  facebook_link = request.form['facebook_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  if request.form['seeking_talent']:
        seeking_talent = True 
  else:
        seeking_talent = False
  seeking_description = request.form['seeking_description']

  try:
      venue = Venue.query.get(venue_id)
      venue.name = name
      venue.city = city
      venue.state = state
      venue.address = address
      venue.phone = phone
      venue.image_link = image_link
      venue.facebook_link = facebook_link
      venue.genres = genres
      venue.website = website
      venue.seeking_talent = seeking_talent
      venue.seeking_description = seeking_description

      db.session.commit()
  except Exception:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash(
        'Error: Venue could not be updated!'
      )  
      abort(400)
  else:
      flash(
        'Venue successfully updated!'
      )
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = ArtistForm()

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  image_link = request.form['image_link']
  facebook_link = request.form['facebook_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  if request.form['seeking_venue']:
        seeking_venue = True 
  else:
        seeking_venue = False
  seeking_description = request.form['seeking_description']

  try:
      artist = Artist(
        name=name,
        city=city,
        state=state,
        phone=phone,
        genres=genres,
        image_link=image_link,
        facebook_link=facebook_link,
        website=website,
        seeking_venue=seeking_venue,
        seeking_description=seeking_description,
      )

      db.session.add(artist)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.') 
      abort(400)
  else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows_data = db.session.query(Artist.name,Artist.image_link,Venue.name, Show.venue_id,Show.artist_id,Show.start_time
      ).filter(Venue.id == Show.venue_id, Artist.id == Show.artist_id)

  for show in shows_data:
      data.append({
        'artist_name': show[0],
        'artist_image_link': show[1],
        'venue_name': show[2],
        'venue_id': show[3],
        'artist_id': show[4],
        'start_time': str(show[5])
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error = False

  try:
      show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time'],
      )

      db.session.add(show)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()

  if error:
      flash('Error: Show could not be listed!')  
      abort(400)
  else:
      flash('Show was successfully listed!')

  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
