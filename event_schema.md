# WordPress Event Plugin

[Capital Nature](http://capitalnature.org/) is hosted on WordPress (WP). The site is using a WP events plugin to populate a calendar with the events we scrape. However, that plugin expects our event data to follow a certain schema, which we document here.

> *Although **latitude** and **longitude** aren't in this table, please capture this data (if possible) when you scrape a page (just comment that part of the code out afterwards). That's because we might want to eventually use that geo-data to creata an events map!*

**Required fields are bolded, although you can fill a missing end time with a valid start time and a missing end date with a valid start date.**

## Schema

|Field Name|Example Data|Field Type|Notes|
|--- |--- |--- |--- |
|**Event Name**|Tacktleneck Fitting|String||
|**Event Description**|I didn't invent the turtleneck, but...|String||
|Event Excerpt|I'm afraid of any apex predator that lived through the K-T Extinction.|String|This is used as the excerpt, while the description is used as the actual content.|
|**Event Start Date**|1965-12-31|Date|Example is for an event on December 31st, 1965.|
|**Event Start Time**|21:30:00|Time|The time of day that the event starts. Example is for an event starting at 9:30pm.|
|**Event End Date**|1966-01-01|Date|Example is for an event ending on January 1st, 1966.|
|**Event End Time**|00:50:00|Time|The time of day that the event ends. Example is for an event ending at 12:50am.|
|**All Day Event**|False|Boolean|When true the event is treated as lasting all day from the beginning of the Start Date to the end of the End Date. The Start/End Time fields are essentially ignored and can be left blank.|
|**Timezone**|America/New_York|String|This should be a valid Timezone string. Timezones can be represented in numerous acceptable ways. You can find a list of acceptable timezones sorted by continent here.|
|Hide from Event Listings|FALSE|Boolean|When true, the event will appear in Month View, but in "List" views like the outright List View, the Photo View, etc.|
|Sticky in Month View|TRUE|Boolean|When true, the event will appear at the top of its corresponding "day" square in the Month View, regardless of other events that day at other times.|
|**Event Venue Name**|Archer's Penthouse|Comma Separated|Must match exactly the Venue Name of a preexisting Venue (see note about multiple venues).|
|**Event Organizers**|Montgomery County|String|Must be the event source. Hardcode this.|
|Event Show Map Link|TRUE|Boolean||
|Event Show Map|TRUE|Boolean||
|**Event Cost**|500|String|Set to 0 for a free event. Leave blank if you do not wish the cost field to appear. Otherwise specify a single number for the event cost. This field is essentially unused when a ticketing plugin is active.|
|**Event Currency Symbol**|$|String|This field is essentially unused when a ticketing plugin is active.|
|Event Currency Position|prefix|Unique|Sets whether the Currency Symbol is a prefix or suffix. Accepts two values "prefix" and "suffix". When left blank the default "prefix" is used. This field is essentially unused when a ticketing plugin is active.|
|Event Phone|+1-326-437-9663|Phone Number||
|**Event Category**|Tacktleneck, Tailor|Comma Separated|Separate multiple categories with commas. You can use an empty string if there aren't any identifiable categories. The example puts this event in two categories: Tacktleneck and Tailor.|
|Event Tags|Valet, Mission ready, PPK|Comma Separated|Separate multiple tags with commas|
|**Event Website**|http://doyounot.com|URL||
|Event Featured Image|http://doyounot.com/wp-content/uploads/thumbs/event.png|URL|This should be a direct URL to the image.|
|Allow Comments|TRUE|Boolean|When true, comments will be allowed on the event.|
|Allow Trackbacks and Pingbacks|FALSE|Boolean|When true, trackbacks and pingbacks will be allowed on the event.|



## Field types
Here's some notes on the field types above:

 - **String** - UTF-8
 - **Boolean** - Accepts boolean values such as true or false, 1 or 0, yes or no. These values are not case sensitive, so TRUE would also be a valid value. When left blank the default option is applied, which is typically false.
 - **Date** - Accepts formatted dates. Preferably use the ISO 8601 date format YYYY-MM-DD as it is unambiguous (ex. 2015-12-31).
 - **Time** - Accepts formatted hours. Preferably use the ISO 8601 format HH:MM:SS (ex. 23:59:59).
 - **URL** - Prefers full URLs with the protocol (ex. https://) included.
 - **Comma Separated** - There is a certain bit of irony with this type. Accepts a comma-separated list of values (ex. "Concert, Barbecue" will be interpreted as the 2 separate values "Concert" and "Barbecue").
 - **Email Address** - Accepts any string, but prefers valid email addresses. Use the regex in `tests/utils` to assert this.
 - **Phone Number** - For proper internationalization include the full phone number with a country code and leading + (ex: +1-800-867-5309)
