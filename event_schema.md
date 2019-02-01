# WordPress Event Plugin

capitalnature.org is hosted on WordPress. The site is using a WP events plugin to populate scraped events. That plugin expects our event data to be in a certain schema, which can be found [here](https://support.theeventscalendar.com/969953-CSV-file-examples-for-importing). I've reproduced the table below for convenience:

|Field Name|Example Data|Field Type|Notes|
|--- |--- |--- |--- |
|Event Name|Tacktleneck Fitting|String||
|Event Description|I <em>didn't</em> invent the turtleneck, but...|HTML||
|Event Excerpt|I'm afraid of any apex predator that lived through the <strong>K-T Extinction.</strong>|HTML|This is used as the excerpt, while the description is used as the actual content.|
|Event Start Date|1965-12-31|Date|Example is for an event on December 31st, 1965.|
|Event Start Time|21:30:00|Time|The time of day that the event starts. Example is for an event starting at 9:30pm.|
|Event End Date|1966-01-01|Date|Example is for an event ending on January 1st, 1966.|
|Event End Time|00:50:00|Time|The time of day that the event ends. Example is for an event ending at 12:50am.|
|All Day Event|FALSE|Boolean|When true the event is treated as lasting all day from the beginning of the Start Date to the end of the End Date. The Start/End Time fields are essentially ignored and can be left blank.|
|Timezone|America/New_York|String|This should be a valid Timezone string. Timezones can be represented in numerous acceptable ways. You can find a list of acceptable timezones sorted by continent here.|
|Hide from Event Listings|FALSE|Boolean|When true, the event will appear in Month View, but in "List" views like the outright List View, the Photo View, etc.|
|Sticky in Month View|TRUE|Boolean|When true, the event will appear at the top of its corresponding "day" square in the Month View, regardless of other events that day at other times.|
|Event Venue Name|Archer's Penthouse|Comma Separated|Must match exactly the Venue Name of a preexisting Venue (see note about multiple venues).|
|Event Organizers|Woodhouse, Chelsea S., 42|Comma Separated|Must match exactly the Organizer Name of a preexisting Organizer, or you can use the Organizer's post ID. You can enter multiple Organizer Names or IDs separated by commas.|
|Event Show Map Link|TRUE|Boolean||
|Event Show Map|TRUE|Boolean||
|Event Cost|500|String|Set to 0 for a free event. Leave blank if you do not wish the cost field to appear. Otherwise specify a single number for the event cost. This field is essentially unused when a ticketing plugin is active.|
|Event Currency Symbol|$|String|This field is essentially unused when a ticketing plugin is active.|
|Event Currency Position|prefix|Unique|Sets whether the Currency Symbol is a prefix or suffix. Accepts two values "prefix" and "suffix". When left blank the default "prefix" is used. This field is essentially unused when a ticketing plugin is active.|
|Event Phone|+1-326-437-9663|Phone Number||
|Event Category|Tacktleneck, Tailor|Comma Separated|Separate multiple categories with commas. The example puts this event in two categories: Tacktleneck and Tailor.|
|Event Tags|Valet, Mission ready, PPK|Comma Separated|Separate multiple tags with commas|
|Event Website|http://doyounot.com|URL||
|Event Featured Image|http://doyounot.com/wp-content/uploads/thumbs/event.png|URL|This should be a direct URL to the image.|
|Allow Comments|TRUE|Boolean|When true, comments will be allowed on the event.|
|Allow Trackbacks and Pingbacks|FALSE|Boolean|When true, trackbacks and pingbacks will be allowed on the event.|
