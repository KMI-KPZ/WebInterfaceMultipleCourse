#!/usr/bin/env python
# coding: utf-8


# In[ ]:
import tornado.web
import pymysql
import rdflib
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
import glob
import socket
import pdb
import logging
import os
import tornado.ioloop

# Database connection
db = pymysql.connect(host='localhost',
                     user='HERE YOU WRITE USER NAME',
                     password='PUT THE PASSWORD FOR YOR DATABASE',
                     db='novel_course')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("novel_course.html", course_id=None, course_name=None, instructor=None, description=None)  # Pass instructor and description to the template

    def post(self):
        try:
            course_name = self.get_argument("course_name")
            lc_name = self.get_argument("lc_name")
            lc_desc = self.get_argument("lc_desc")

            # Insert information into the courses table
            cursor = db.cursor()
            cursor.execute("INSERT INTO Courses (course_name) VALUES (%s)", (course_name,))
            db.commit()

            # Get the auto-generated course ID
            course_id = cursor.lastrowid

            # Insert lc information into the LearningComponents table
            cursor.execute("INSERT INTO LearningComponents (course_id, lc_name, lc_desc) VALUES (%s, %s, %s)",
                           (course_id, lc_name, lc_desc))
            db.commit()

            # Update RDF
            update_rdf(course_id)

            self.render("novel_course.html", course_id=course_id, course_name=course_name, instructor=None, description=None)  # Pass instructor and description to the template
        except Exception as e:
            logging.error("Error occurred in MainHandler post method: %s" % str(e))




class SaveSettingsHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            consumer_key = self.get_argument("consumer_key")
            consumer_secret = self.get_argument("consumer_secret")
            enable_grades = self.get_argument("enable_grades", default=None)
            launch_url = self.get_argument("launch_url")

            cursor = db.cursor()
            cursor.execute("INSERT INTO LTI_settings (course_id, consumer_key, consumer_secret, enable_grades, launch_url) VALUES (101, %s, %s, %s, %s)",
                           (consumer_key, consumer_secret, enable_grades, launch_url))
            db.commit()
        except Exception as e:
            logging.error("Error occurred in SaveSettingsHandler post method: %s" % str(e))

        pdb.set_trace()

        self.write("Settings are saved")


class SaveLCHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            lc_course_name = self.get_argument("lc_course_name")
            lc_name = self.get_argument("lc_name")
            lc_desc = self.get_argument("lc_desc")

            # Save LC information to the database
            cursor = db.cursor()
            cursor.execute("INSERT INTO LearningComponents (course_name, lc_name, lc_desc) VALUES (%s, %s, %s)",
                           (lc_course_name, lc_name, lc_desc))
            db.commit()

            # update RDF for any changes
            update_rdf(lc_course_name)

            self.write("LC information is saved")
        except Exception as e:
            logging.error("Error occurred in SaveLCHandler post method: %s" % str(e))


# Update the AllCoursesHandler get method for retrieving data
class AllCoursesHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            cursor = db.cursor()
            cursor.execute("SELECT course_id, course_name FROM Courses")
            courses = cursor.fetchall()

            course_data = []
            for course_id, course_name in courses:
                # Get the count of learning components for each course
                cursor.execute("SELECT COUNT(*) FROM LearningComponents WHERE course_id = %s", (course_id,))
                lc_count = cursor.fetchone()[0]
                course_data.append({"course_id": course_id, "course_name": course_name, "lc_count": lc_count})

            self.render("all_courses.html", courses=course_data)
        except Exception as e:
            logging.error("Error occurred in AllCoursesHandler get method: %s" % str(e))


class CourseHandler(tornado.web.RequestHandler):
    def get(self, course_name):
        try:
            # read RDF file for the specific course
            file_path = f"{course_name}.rdf"
            graph = rdflib.Graph()
            graph.parse(file_path, format="xml")

            #retrieve the LC from RDF graph
            oer = rdflib.Namespace("http://oerschema.org/LearningComponent/")
            lc_list = []
            for lc_uri in graph.subjects(rdflib.RDF.type, oer.LearningComponent):
                lc_name = graph.value(lc_uri, oer.Course)
                lc_desc = graph.value(lc_uri, oer.forCourse)
                lc_list.append((lc_name, lc_desc))

            self.render("course.html", course_name=course_name, lc_list=lc_list)
        except Exception as e:
            logging.error("Error occurred in CourseHandler get method: %s" % str(e))


class UpdateLCHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            lc_id = self.get_argument("lc_id")
            lc_name = self.get_argument("lc_name")
            lc_desc = self.get_argument("lc_desc")

            # Update the learning component in the database
            cursor = db.cursor()
            cursor.execute("UPDATE LearningComponents SET lc_name = %s, lc_desc = %s WHERE id = %s",
                           (lc_name, lc_desc, lc_id))
            db.commit()

            # Update RDF
            cursor.execute("SELECT course_name FROM LearningComponents WHERE id = %s", (lc_id,))
            lc_course_name = cursor.fetchone()[0]
            update_rdf(lc_course_name)

            self.redirect("/course")  # Redirect back to the course page
        except Exception as e:
            logging.error("Error occurred in UpdateLCHandler post method: %s" % str(e))


def update_rdf(course_name):
    try:
        # create the RDF graph and namespace
        graph = rdflib.Graph()
        oer = rdflib.Namespace("http://oerschema.org/LearningComponent/")

        # load existing RDF data, if any
        file_path = f"{course_name}.rdf"
        if os.path.exists(file_path):
            graph.parse(file_path, format="xml")

        # Remove all existing LC triples from the graph in case of mistakes
        lc_uri = oer[course_name.replace(" ", "_")]
        graph.remove((lc_uri, None, None))

        # Retrieve LC information from the database
        cursor = db.cursor()
        cursor.execute("SELECT lc_name, lc_desc FROM LearningComponents WHERE course_name = %s", (course_name,))
        lc_rows = cursor.fetchall()

        # Add LC triples to the graph
        for lc_name, lc_desc in lc_rows:
            graph.add((lc_uri, rdflib.RDF.type, oer.LearningComponent))
            graph.add((lc_uri, oer.Course, rdflib.Literal(lc_name)))
            graph.add((lc_uri, oer.forCourse, rdflib.Literal(lc_desc)))

        # Serialize the updated RDF graph to the file
        graph.serialize(destination=file_path, format="xml")
    except Exception as e:
        logging.error("Error occurred during RDF update: %s" % str(e))


def make_app():
    try:
        return tornado.web.Application([
            (r'/', MainHandler),
            (r'/save_settings', SaveSettingsHandler),
            (r'/save_lc', SaveLCHandler),
            (r'/all_courses', AllCoursesHandler),
            (r'/course/([^/]+)', CourseHandler),
            (r'/update_lc', UpdateLCHandler),
        ], template_path=os.path.dirname(__file__))
    except Exception as e:
        logging.error("Error occurred in make_app function: %s" % str(e))



logging.basicConfig(filename='error.log', level=logging.ERROR)

if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    host = socket.gethostbyname(socket.gethostname())
    link = f"http://{host}:8080/"
    print(f"Server is running at {link}")

    tornado.ioloop.IOLoop.current().start()
