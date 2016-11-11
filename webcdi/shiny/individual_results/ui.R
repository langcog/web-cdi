#
# This is the user-interface definition of a Shiny web application. You can
# run the application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
# 
#    http://shiny.rstudio.com/
#

library(shiny)

# Define UI for application that draws a histogram
shinyUI(fluidPage(
  
  # Application title
  titlePanel("Your CDI Results"),
  fluidRow( 
    column(7, plotOutput("predicted_vocab")),
    column(5, h2(textOutput("numwords_text")))
    ),
  
  fluidRow(
    column(7, plotOutput("word_categories_chart")),
    column(5, h2(textOutput("word_categories_text")))
    ),

  fluidRow( 
    h2(textOutput("hardest_word"), align = "center")
    ),
  
  tags$head(
    tags$style(HTML("
                    .shiny-output-error-validation {
                    color: green;
                    font-size: 200%;
                    text-align: center;
                    }
                    "))
    )
    

))
