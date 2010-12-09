import cgi
import datetime
import wsgiref.handlers
import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.api import mail
from google.appengine.ext.webapp import template

class Shoutout(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)


class MainHandler(webapp.RequestHandler):
   
    owner_email = 'example@gmail.com'

    def post(self):
        shoutout = Shoutout()

        #self.response.out.write(db.delete(self.request.get("key"))
        if users.is_current_user_admin() and self.request.get("delete"):

            id = int(self.request.get('id'))
            mykey = db.Key.from_path('Shoutout', id)
        
           # db.delete( db.GqlQuery("select __key__ from Shoutout" ) )
            db.delete(mykey)
            self.redirect('/')
            return
            

        if users.get_current_user():
            shoutout.author = users.get_current_user()

        shoutout.content = self.request.get("shoutout")
        shoutout.put()
        self.redirect('/')

        author_name = 'anonymouse'
        if users.get_current_user():
            author_name = users.get_current_user().nickname()


        if xmpp.get_presence(self.owner_email):
            msg = author_name + " sent you this shout : " + self.request.get("shoutout")
            status_code = xmpp.send_message(self.owner_email, msg)

        chat_message_sent = (status_code != xmpp.NO_ERROR)

        if not chat_message_sent:

            message = mail.EmailMessage(sender="Shoutout bot", subject="new shout")

            message.to = self.owner_email
            message.body = self.request.get("shoutout")
            message.send()

    
    def get(self):
        user = users.get_current_user()
        is_admin = False

        path = os.path.join("shoutout.html")

        if user:            
            logouturl = users.create_logout_url(self.request.uri)
            greeting = "Hello, "+user.nickname() +" -- <a href='" + logouturl + "'>logout</a>"

            if users.is_current_user_admin():
                is_admin= True 

        else:
            loginurl = users.create_login_url(self.request.uri)

            greeting = "Hello, buddy :) . wanna <a href='" + loginurl  +"'>login?</a>"

        shouts = db.GqlQuery("select * from Shoutout order by date desc limit 10")

        template_values = {
            "greeting": greeting,
            "shouts": shouts,
            "is_admin":is_admin
        }
        
        self.response.out.write(template.render(path, template_values))






application = webapp.WSGIApplication([
  ('/', MainHandler),
  ('/sign', MainHandler)
  ], debug=True)
 
def main():
    wsgiref.handlers.CGIHandler().run(application)
 
if __name__ == '__main__':
    main()

