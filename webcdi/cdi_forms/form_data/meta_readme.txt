Meta is a json file descriptor format for the CDI csv files. 
It contains a list of Parts, each of which contain a list of types.

There is no mention of Part in the csv file, but the "id" field of each type in the json file corresponds to the "type" field in the csv file. 
Each part has an id and a title.

Each type is guranteed to have an id, title and type (this type is not to be confused with the previous type, this one corresponds to the type of response to be collected, (checkbox, radiobuttons etc). Text is an optional field in each type which corresponds to the textual description in a few types. 

The application level logic of conditional completion (the part which is to be completed only when word combination has begun) is captured in the view rather than the json file. 


