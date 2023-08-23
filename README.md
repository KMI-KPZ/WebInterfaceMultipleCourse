## User-friendly web-interface to save and analyze provided data 
The use of Tornado for the server and the combination of local databases and RDF stores ensures efficient data storage
and retrieval. 

The script creates a web interface for managing courses and learning components.
It allows users to create courses, add learning components to courses, update LTI settings, 
view a list of all courses, see details about specific courses and their learning components,
and update learning component information. 
The script integrates database storage with RDF representation for efficient data management.

## Requirements

- tornado
- MySQL, SQL or any database of you choice
- rdflib
- pymysql

## Usage
Make sure that every file you use is in the same directory. The log file with errors if any will be generated automatically. 
To perform the action ensure that all the libraries are installed and you plug in the name of the database and password correctly
(in the script 'app.py' there is an instruction on where you are supposed to do that). 

Be careful with the file's names as they also should be changed according to your choice, or simply name it according to the code.

## Overall idea and Handler description

This Python script is a Tornado web application. 
The script imports various modules necessary for database connection (pymysql),
RDF handling (rdflib), web development (tornado), and logging.

- Database connection: It establishes a connection to a MySQL database named 'novel_course'.
- Update RDF Function (update_rdf): The function updates RDF data for a course and its learning components.
  It creates or modifies an RDF graph, retrieves data from the database, and serializes the graph to an XML RDF file.
- App Initialization (make_app): Sets up the Tornado application by specifying URL patterns and associated handlers.
- Logging Configuration: Configures logging to record errors in the 'error.log' file.

Shortly about the Handlers. The script defines multiple request handlers to manage different HTTP endpoints:

- MainHandler: Manages the main page, presenting forms for creating new courses and learning
  components and processing submissions.
- SaveSettingsHandler: Saves LTI settings linked to a course.
- SaveLCHandler: Records learning component details.
- AllCoursesHandler: Retrieves and displays a list of all courses created.
- CourseHandler: Displays specifics of a chosen course and its learning components.
- UpdateLCHandler: Takes care of updating learning component information.
  
  


