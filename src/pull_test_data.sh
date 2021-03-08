#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

PARENTDIR="$(dirname $SCRIPTPATH)"

echo "Please input the test project UUID"

read project_uuid

pattern="^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"

if [[ $project_uuid =~  $pattern ]]
    then
        valid=true
        echo "yes"
    else
        echo "Please insert a valid uuid"
        valid=false
    fi

if [ $valid = true ]
    then
        echo "Verifying it's a valid project UUID"
        status=$(curl --write-out "%{http_code}\n" --silent --output /dev/null https://api.ingest.staging.archive.data.humancellatlas.org/projects/search/findByUuid?uuid=$project_uuid)
        echo $status
        if [ $status -lt 400 ]
            then
                echo "Found project in ingest"
            else
                echo "Project not found in ingest"
            fi
    fi

if [ $valid = true ] & [ $status -lt 400 ]
    then
        echo "Creating branch for release, please make sure you are in master"
        today=$( date +'%d/%m/%Y' )
        git checkout master
        git pull
        git checkout -b release-data-$today

        echo "Pushing the dataset to the branch, please make sure you have gsutil configured"
        cd $PARENTDIR
        if [ ! -d "tests" ]
        then
            mkdir tests
        fi
        cd tests

        gsutil -m rsync -r gs://broad-dsp-monster-hca-dev-ebi-staging/staging/$project_uuid $project_uuid

        echo "Release of new data, $project_uuid-$today. Pushing to branch and creating PR"

        git commit -a -m "Added new data: $project_uuid, corresponding to release on $today"
        git push origin release-data-$today
        echo "Please go to the following website and fill in the details of the PR: https://github.com/HumanCellAtlas/schema-test-data/compare/master...release-data-$today"


    else
        echo "Something went wrong, probably the UUID is not correct"
    fi
