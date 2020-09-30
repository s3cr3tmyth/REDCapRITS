readfile <- as.data.frame(read.csv("R/tests/testthat/data/ExampleProject_DATA_2018-06-07_1129.csv"))
meta <- as.data.frame(read.csv("R/tests/testthat/data/ExampleProject_DataDictionary_2018-06-07.csv"))

View(readfile)
View(meta)

#forms = c("repeating", "all")
forms = "repeating"
primary_table_name = "sale"

forms <- match.arg(forms)


if(any(is.na(readfile$redcap_repeat_instrument))) {
  readfile$redcap_repeat_instrument <- ifelse(
    is.na(readfile$redcap_repeat_instrument),
    "",
    as.character(readfile$redcap_repeat_instrument)
  )
}

View(readfile)

vars_in_data <- names(readfile)
vars_in_data

# Standardize variable names for metadata
names(meta) <- meta_names

meta_in_data <- names(meta)



meta <- rapply(meta,as.character,classes = "factor",how = "replace")


# Function 1 Start


fields <- meta[!meta$Field.Type %in% c("descriptive", "checkbox"), c("Field.Name", "Form.Name")]
fields

form_names <- unique(meta$Form.Name)
form_names


form_complete_fields <- data.frame(
  Field.Name = paste0(form_names, "_complete"),
  Form.Name = form_names,
  stringsAsFactors = FALSE
)

View(form_complete_fields)


fields <- rbind(fields, form_complete_fields)


temp <- paste0(form_names, "_timestamp")

timestamps <- intersect(vars_in_data, temp)

if (length(timestamps)) {
  
  timestamp_fields <- data.frame(
    Field.Name = timestamps,
    Form.Name = sub("_timestamp$", "", timestamps),
    stringsAsFactors = FALSE
  )
  
  fields <- rbind(fields, timestamp_fields)
  
}
fields


if (any(meta$Field.Type == "checkbox")) {
  
  checkbox_basenames <- meta[
    meta$Field.Type == "checkbox",
    c("Field.Name", "Form.Name")
  ]
  
  checkbox_fields <-
    do.call(
      "rbind", apply(checkbox_basenames,1,function(x, y) data.frame(
        Field.Name = y[grepl(paste0("^", x[1], "___((?!\\.factor).)+$"), y, perl = TRUE)],
        Form.Name = x[2],
            stringsAsFactors = FALSE,
            row.names = NULL),
        y = vars_in_data))
  
  fields <- rbind(fields, checkbox_fields)
}

vars_in_data
fields

# Process ".*\\.factor" fields supplied by REDCap's export data R script
if (any(grepl("\\.factor$", vars_in_data))) {
  
  factor_fields <-
    do.call(
      "rbind",
      apply(
        fields,
        1,
        function(x, y) {
          field_indices <- grepl(paste0("^", x[1], "\\.factor$"), y)
          if (any(field_indices))
            data.frame(
              field_name = y[field_indices],
              form_name = x[2],
              stringsAsFactors = FALSE,
              row.names = NULL
            )
        },
        y = vars_in_data
      )
    )
  
  fields <- rbind(fields, factor_fields)
  
}

fields


### Function I end

universal_fields <- c(
  vars_in_data[1],
  grep(
    "^redcap_(?!(repeat)).*",
    vars_in_data,
    value = TRUE,
    perl = TRUE
  )
)


if ("redcap_repeat_instrument" %in% vars_in_data) {

  repeat_instrument_fields <- grep(
    "^redcap_repeat.*",
    vars_in_data,
    value = TRUE
  )

  subtables <- unique(readfile$redcap_repeat_instrument)
  subtables <- subtables[subtables != ""]
  

  out <- split.data.frame(readfile, readfile$redcap_repeat_instrument)
  primary_table_index <- which(names(out) == "")
  
  
  if (forms == "repeating" && primary_table_name %in% subtables) {
    warning("The label given to the primary table is already used by a repeating instrument. The primary table label will be left blank.")
    primary_table_name <- ""
  } else if (primary_table_name > "") {
    names(out)[[primary_table_index]] <- primary_table_name
  }
  
  # Delete the variables that are not relevant
  for (i in names(out)) {
    
    if (i == primary_table_name) {
      
      out_fields <- which(
        vars_in_data %in% c(
          universal_fields,
          fields[!fields[,2] %in% subtables, 1]
        )
      )
      out[[primary_table_index]] <- out[[primary_table_index]][out_fields]
      
    } 
    else {
      
      out_fields <- which(
        vars_in_data %in% c(
          universal_fields,
          repeat_instrument_fields,
          fields[fields[,2] == i, 1]
        )
      )
      out[[i]] <- out[[i]][out_fields]
      
    }
    
  }
  if (forms == "all") {
    
      out <- c(
        split_non_repeating_forms(
          out[[primary_table_index]],
          universal_fields,
          fields[!fields[,2] %in% subtables,]
        ),
        out[-primary_table_index]
      )
      
    }
    
} else {
    
    out <- split_non_repeating_forms(records, universal_fields, fields)
  
}
  
#out[[primary_table_index]]
#universal_fields
j <- fields[!fields[,2] %in% subtables,]
j

forms <- unique(j[[2]])
forms

x <- lapply(
  forms,
  function (x) {
    out[[primary_table_index]][names(out[[primary_table_index]]) %in% union(universal_fields, fields[fields[,2] == x,1])]
  })

x
forms
universal_fields

names(out[[primary_table_index]])

length(out[[primary_table_index]])
length(x[[2]])

