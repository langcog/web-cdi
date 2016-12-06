

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
    h2(textOutput("hardest_word"), align = "center"),
     br(),
     h2(textOutput("completion_code"), align = "center")
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
