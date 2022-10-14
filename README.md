# schema-test-data
This repository is for the test [meta]data associated with the latest updates of the HCA metadata schema.

# Brief SOP on generating test data 

1. Download the excel spreadsheet located in this folder (schema_test_data.xlsx) and modify it to include the new metadata-schema changes.
If you are adding new data:
- **PLEASE REMEMBER TO INCLUDE THE NEW DATA IN THE HCA-UTIL AREA STATED IN THE NEXT STEP**
- use dummy files for fastqs, for example a copy of an existing one (see step 2)

2. Use the modified excel spreadsheet to create a new project in the [staging environment in ingest](https://staging.contribute.data.humancellatlas.org). The necessary analysis_files are located in an hca-util area, obtainable by executing the following command: `hca-util list -b | grep "schema-test-data"`

3. Wait until the metadata is validated, select the upload area and sync the files to the new submission.
4. Export the data and metadata.


5. Copy the Project UUID of the exported project. 
6. Run the pull_test_data.sh script using the following command: 
   ```
   sh pull_test_data.sh 
   ```
When asked for a project UUID, enter the project uuid of the exported project. Running this script generates a new branch of the schema-test-data repo titled release-data-[date]. This new branch has the data of the exported project in its ‘tests’ folder. 

7. Switch to this branch, and run the post_process.py script using the following command, passing the argument of the ‘tests’ folder. Ensure you are in the src folder when running this command:
    ```
    python3 post_process.py ../tests
    ```
    
8. A new folder within `src/` will be created, called `tests`. Delete the root `tests` folder and move the `src/tests` folder to the root of the repository
9. Delete the newly created `src/temp_data` folder
10. Push the changes made to this branch to Github
11. Ensure you update the excel spreadsheet located in the schema-test-data repo with the up-to-date modified spreadsheet for the next cycle of generating test data 
12. Create a PR from the branch to master - this will include the modified test data, and the diff should show only the files that have been changed as a result of the metadata schema change.
Include in the PR a description of what the test data is being used for and reference to the issue it's addressing
