#
# This is the server logic of a Shiny web application. You can run the 
# application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
# 
#    http://shiny.rstudio.com/
#

library(shiny)
library(dplyr)
library(ggplot2)
library(gtable)
library(grid)
library(langcog)
library(feather)
library(stringr)
library(ggrepel)
source("access-webcdi.R")
mode="local"
src <- connect_to_webcdi(mode=mode)
word_cats <- read.csv("word_categories.csv")
theme_set(theme_mikabr(base_size = 12))


english_wg_prod <- read_feather("data/eng_wg_production_aoas.feather")
english_wg_und <- read_feather("data/eng_wg_comprehension_aoas.feather")
english_ws_prod <- read_feather("data/eng_ws_production_aoas.feather")
english_pred_vocab <- read_feather("data/predicted_vocab_English_WG_WS.feather")


# Define server logic required to draw a histogram
shinyServer(function(input, output, session) {
  
  # Store in a convenience variable
  hash_id <- reactive({
    parseQueryString(session$clientData$url_search)
        })
  
  admin_info <- reactive({get_common_table(src, "researcher_UI_administration") %>% as.data.frame() %>% filter(url_hash==hash_id())
  })
  
  server_id <- reactive({
    admin_info()$id
  })
  
  study_id <- reactive({
    admin_info()$study_id
  })
  
  study_info <- reactive({
    get_common_table(src, "researcher_UI_study") %>% as.data.frame() %>% filter(id == study_id())
  })
  
  background_info <- reactive({
    get_common_table(src, "cdi_forms_backgroundinfo") %>% as.data.frame() %>% filter(administration_id == server_id())
  })
  
  study_items <- reactive({
    get_common_table(src, paste("cdi_forms", tolower(study_info()$instrument_id), sep="_")) %>% rename(item_ID = itemID)
    
  })
  study_answers <- reactive({
    get_common_table(src, "researcher_UI_administration_data") %>% as.data.frame() %>% filter(administration_id == server_id())
  })
  study_data <- reactive({
    left_join(study_items(), study_answers(), copy=T) %>% mutate(numvalue = ifelse(value %in% c("produces", "often"), 2,
                                                                                   ifelse(value %in% c("yes","understands", "complex", "sometimes"), 1,0)))
    })
  
  study_word <- reactive({
    filter(study_data(), item_type == "word")
  })
  
  study_word_categories <- function() {
    words <- as.data.frame(study_word()) %>% group_by(category) %>% summarise(mean_produced = 100*mean(ifelse(numvalue ==2, 1,0)), mean_understood = 100*mean(ifelse(numvalue >= 1, 1,0)))
    names(words) <- c("Word Category","% of Words Said", "% of Words Understood")
    a <- as.data.frame(study_word())
    num_understood <- sum(a$numvalue == 1)
    if (num_understood == 0) {
      words$`% of Words Understood` <- NULL
    }
    words <- words[order(words$`% of Words Said`),]
    for (i in 1:nrow(words)){
      if (words$`Word Category`[i] %in% word_cats$id){
        words$`Word Category`[i] = as.character(word_cats$category[match(words$`Word Category`[i], word_cats$id)])
      }
    }
    return(words)
  }
  
  most_unique_produced <- function() {
    words_produced <- filter(as.data.frame(study_data()), item_type == "word" & numvalue == 2)
    if (study_info()$instrument_id == "English_WG") {
      aoa <- english_wg_prod
    } else if (study_info()$instrument_id == "English_WS"){
      aoa <- english_ws_prod
    }
    a <- inner_join(words_produced,aoa)
    hardest_words <- a$item[a$aoa == max(a$aoa, na.rm = T)]
    return(hardest_words[1])
  }
  
  predicted_vocab <- function() {
    words <- as.data.frame(study_word())
    num_produced <- sum(words$numvalue == 2)
    instrument_curves <- english_pred_vocab %>% filter(Instrument == study_info()$instrument_id)
    child_age <- background_info()$age
    age_compare <- instrument_curves %>% filter(age == child_age)
    closest_quantile <- which.min(abs(age_compare$predicted - num_produced))
    paste(closest_quantile)
  }
  
  
  output$predicted_vocab <- renderPlot({
    words <- as.data.frame(study_word())
    num_produced <- sum(words$numvalue == 2)
    instrument_curves <- english_pred_vocab %>% filter(Instrument == study_info()$instrument_id)
    child_age <- background_info()$age
    age_compare <- instrument_curves %>% filter(age == child_age)
    closest_quantile <- age_compare$quantile[which.min(abs(age_compare$predicted - num_produced))]
    curveToPlot <- instrument_curves %>% filter(quantile == closest_quantile)
    currentPoint <- curveToPlot %>% filter(age == child_age)
    growth <- ggplot(curveToPlot, aes(x = age, y = predicted)) + geom_line(colour = "#9471f2", size = 2) + geom_point(data = currentPoint, aes(x = age, y = predicted), size = 6, colour = "#2dbc74")
    growth <- growth + xlab("Age (in Months)") + ylab("Predicted Size of Spoken Vocabulary") 
    growth <- growth + ggtitle("Predicted Growth of Vocabulary Over Time") 
    growth <- growth + geom_text_repel(data=currentPoint, aes(age, predicted, label = "Current Vocabulary Size"), nudge_x = 1, size = 5,  point.padding = unit(1, "lines")) 
    growth <- growth + scale_x_continuous(limits=c((min(curveToPlot$age)-0.5),(max(curveToPlot$age)+0.5)), breaks = seq(min(curveToPlot$age), max(curveToPlot$age), 1))
    print(growth)
    })
  
  output$numwords_text <- renderText({
    words <- as.data.frame(study_word())
    num_produced <- sum(words$numvalue == 2)
    num_understood <- sum(words$numvalue == 1)
    if (num_understood > 0) {
      paste("My baby says", num_produced, "words and understands",num_understood + num_produced,"words.", sep=" ")
    } else{
      paste("My baby says", num_produced, "words.", sep=" ")
    }
  })
  
  output$numwords_chart <- renderPlot({
    words <- as.data.frame(study_word())
    words$value[is.na(words$value)] <- "Neither Said nor Understood"
    words$value[words$value == "produces"] <- "Produces"
    words$value[words$value == "understands"] <- "Understands"
    pie <- ggplot(words, aes(x = factor(1), fill = factor(value))) +
      geom_bar(width = 1) + coord_polar(theta = "y") + xlab("% of Words") + ggtitle("% of Words on Assessment")
    print(pie)
  })
  
  output$word_categories_text <- renderText({
    categories <- study_word_categories()
    best_produced <- categories$`Word Category`[categories$`% of Words Said` == max(categories$`% of Words Said`)]
    if (!is.null(categories$`% of Words Understood`)) {
      best_understood <- categories$`Word Category`[categories$`% of Words Understood` == max(categories$`% of Words Understood`)]
      paste0("My baby says the most words in the \"",best_produced[1],"\" category and understands the most words in the \"",best_understood[1],"\" category.")
    } else {
      paste0("My baby says the most words in the \"",best_produced[1],"\" category.")
      
    }
  })
  
  output$word_categories_chart <- renderPlot({
    categories <- study_word_categories()
    bar_produced <- ggplot(categories, aes( x = `Word Category`, y =`% of Words Said`, fill = `Word Category`)) + ylab("% of Words\nSaid") + geom_bar(stat = "identity")  + theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position="none")
    if (!is.null(categories$`% of Words Understood`)) {
      bar_understood <- ggplot(categories, aes( x = `Word Category`, y =`% of Words Understood`, fill = `Word Category`)) + ylab("% of Words\nUnderstood") + geom_bar(stat = "identity") + theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position="none")
      bar_produced <- bar_produced + theme(axis.title.x=element_blank(), axis.text.x=element_blank(), axis.ticks.x=element_blank())
      bars_up <- rbind(ggplotGrob(bar_produced), ggplotGrob(bar_understood),  size="first")
      grid.newpage()
      grid.draw(bars_up)
      } else {
      print(bar_produced)
    }
    
  })
  
  output$hardest_word <- renderText({
    paste0("The hardest word that my baby says is \"",most_unique_produced(),"\".")
  })
  
  output$allVariables <- renderText(
    paste(hash_id(), server_id(), sep="\n")
  )
  
 # output$studyData <- renderTable(
 #   study_word()
 # )
  
})
