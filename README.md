# Coursera-Final-Project
This is the final project for the IBM Data Science Zertifikat 

# Description
The goal of this project is to find out in which borough it makes sense to open up a new restaurant. More over I want to find out which kind of restaurant makes sense. The city of choice is my home town Darmstadt, Germany.
So in the first step I will identify a good borough for opening a new restaurant. As criteria I am going to take the amount of restaurants per inhabitants in a borough. 
As the second step I will identify what kind of restaurants makes sense to open in this borough. 

As a last add on, I will make a recommendation for each borough, what kind of restaurant makes sense to open there

# Data
I scrap the relevant information about the relevenat the borough from https://de.wikipedia.org/wiki/Liste_der_Stadtteile_von_Darmstadt. I am only going to focus on boroughs in the city itself, on the webpage under "Darmstadt Innenstadt" - not districts from the further city area. 
To receive the location Data I use the python lib "geocode". 
To check the amount and kind of restaurants I use the Foursquare Api. 
