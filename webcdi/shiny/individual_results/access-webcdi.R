connect_to_webcdi <- function(mode = "remote") {
  
  assertthat::assert_that(is.element(mode, c("local", "remote")))
  address <- switch(mode,
                    local = "localhost",
                    remote = "52.32.108.131")
  
  src <- dplyr::src_postgres(host = address, dbname = "webcdi-admin",
                          user = "webcdi-admin", password = "first5words")
  return(src)
}

get_common_table <- function(src, name) {
  common_table <- dplyr::tbl(src, name)
  return(common_table)
}

