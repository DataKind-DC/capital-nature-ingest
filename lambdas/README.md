# Capital Nature Ingest Lambda Packages

## How to Create a New Package

1. Create a new branch with your name and the Capital Nature source, e.g. `alexidev-casey_trees`
2. Make a new directory in this `lambdas/` directory and name it after the source
3. Copy the contents of the ans directory to your new directory

  Example:
  ```bash
  git checkout -b alexidev-casey_trees
  mkdir casey-trees && cp -r ans/ casey-trees/
  ```

4. Update the `lambda_function.py` code to handle your source. The code in the ans example includes a function `handle_ans_page` which should be replaced with code specific to the source you are working on, but the output object should have the same structure. The output schema we are using at the moment (this could change once we start to import data into the site) is:

  ```json
  [
    {
      "website": "https://anshome.org/events/saturday-beginner-bird-walk-winter/", 
      "startDate": "2019-1-5", 
      "endDate": "2019-1-5", 
      "startTime": "8:00 am", 
      "latitude": 39.003311, 
      "venueName": "Woodend Nature Sanctuary", 
      "endTime": "9:00 am", 
      "longitude": -77.067332, 
      "venueAddress": "8940 Jones Mill Road, Chevy Chase, MD 20815, USA"
    }
  ]
  ```

5. Note that if the code requires any additional libraries (right now the ans example only requires beautifulsoup and requests), you should include them in your directory's requirements.txt.

6. You can test the code locally by uncommenting the code at the bottom and updating `event` object to match your source. E.g. for casey trees:

  ```python
  event = {
    'url': 'https://caseytrees.org/events/',
    'source_name': 'casey-trees'
  }
  ```

  ```bash
  python lambda_handler.py
  ```

7. Open a pull request
