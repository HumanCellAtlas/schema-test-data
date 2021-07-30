# schema-test-data
This repository is for the test [meta]data associated with the latest updates of the HCA metadata schema.

# Brief SOP on generating test data 

1. Download the excel spreadsheet located in this folder (schema_test_data.xlsx) and modify it to include the new metadata-schema changes. 
2. Use the modified excel spreadsheet to generate a new project in ingest. The necessary analysis_files are located in the below hca-util area. Sync the files to the S3 bucket, and export the data and metadata to the staging area. 

Created upload area with UUID 428794cc-cec2-4a98-8649-76accda2304f and name schema-test-data
- 428794cc-cec2-4a98-8649-76accda2304f/AP1_file.h5ad
- 428794cc-cec2-4a98-8649-76accda2304f/AP2_file.h5ad


3. Copy the Project UUID of the exported project. 
4. Run the pull_test_data.sh script using the following command: 

  sh pull_test_data.sh 

When asked for a project UUID, enter the project uuid of the exported project. Running this script generates a new branch of the schema-test-data repo titled release-data-[date]. This new branch has the data of the exported project in its ‘tests’ folder. 

5. Switch to this branch, and run the post_process.py script using the following command, passing the argument of the ‘tests’ folder:

python3 post_process.py [schema-test-data/tests]

6. Push the changes made to this branch to Github
7. Create a PR from the branch to master - this will include the modified test data, and the diff should show only the files that have been changed as a result of the metadata schema change 
8. Ensure you update the excel spreadsheet located in the schema-test-data repo with the up-to-date modified spreadsheet for the next cycle of generating test data 
