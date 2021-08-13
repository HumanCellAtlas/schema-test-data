# schema-test-data
This repository is for the test [meta]data associated with the latest updates of the HCA metadata schema.

# Brief SOP on generating test data 

1. Download the excel spreadsheet located in this folder (schema_test_data.xlsx) and modify it to include the new metadata-schema changes. 
2. Use the modified excel spreadsheet to create a new project in the [staging environment in ingest](https://staging.contribute.data.humancellatlas.org). The necessary analysis_files are located in an hca-util area, obtainable by executing the following command: `hca-util list -b | grep "schema-test-data"`

3. Wait until the metadata is validated, select the upload area and sync the files to the new submission.
4. Export the data and metadata.


5. Copy the Project UUID of the exported project. 
6. Run the pull_test_data.sh script using the following command: 

  sh pull_test_data.sh 

When asked for a project UUID, enter the project uuid of the exported project. Running this script generates a new branch of the schema-test-data repo titled release-data-[date]. This new branch has the data of the exported project in its ‘tests’ folder. 

7. Switch to this branch, and run the post_process.py script using the following command, passing the argument of the ‘tests’ folder:
    ```
    python3 post_process.py [schema-test-data/tests]
    ```
8. Push the changes made to this branch to Github
9. Create a PR from the branch to master - this will include the modified test data, and the diff should show only the files that have been changed as a result of the metadata schema change 
10. Ensure you update the excel spreadsheet located in the schema-test-data repo with the up-to-date modified spreadsheet for the next cycle of generating test data 
