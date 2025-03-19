# summer-school-setup

Artifacts to automate cluster setup for summer school workshop.

Instructions for OpenShift AI artifact creation from the CLI were copied from [here](https://github.com/stratus-ss/openshift-ai/blob/main/docs/rendered/OpenShift_AI_CLI.md#workbench-basics)

## Setting up the workshop environment for users

**Important** If you haven't already created the cluster and set up the
custom workbench image, do those steps first by following the instructions
in the second half of this README.

### Users List

A list of GitHub usernames for workshop participants can be found in [users_list.txt](users_list.txt). To
prepare a workshop for an additional user, first add their GitHub username to that file in a new line.

**Important** In order to access the workshop cluster, the user must also be added to
[our GitHub organization](https://github.com/orgs/ai-for-good-workshop/people) and
accept the resulting invite. If you need to bulk add workshop participants,
you can run the [manage_org_membership.py](manage_org_membership.py) sript. This
requires a file, `.github_token.txt` which contains a GitHub token with permissions to
write the organization membership.

### Log Into the OpenShift Cluster

The script that you'll run in the next step depends on having a local client session
connected to the workshop OpenShift cluster.

First, [install the OpenShift Client tool](https://docs.redhat.com/en/documentation/openshift_container_platform/4.7/html/cli_tools/openshift-cli-oc#cli-about-cli_cli-developer-commands)

Then, browse to the [OpenShift cluster console](https://console-openshift-console.apps.rosa.ai4g-workshop.bscm.p3.openshiftapps.com/).
Next, click your username in the top right of the window and select `Copy login command`.

This will open another tab. Click the `Display Token` button, then copy the `Log in with this token`
command. It will look like:

```
oc login --token=sha256~Ewz...N7I --server=https://api.ai4g-workshop.bscm.p3.openshiftapps.com:443
```

Run this command in a terminal. If successful, the output should resemble the following:

```
Logged into "https://api.ai4g-workshop.bscm.p3.openshiftapps.com:443" as "$YOUR_USERNAME$" using the token provided.

You have access to 88 projects, the list has been suppressed. You can list all projects with 'oc projects'

Using project "default".
```

### Run the Workshop Setup Script

First, you will need to set two environment variables, `S3_KEY`, and `S3_SECRET` that
will be used to create OpenShift secrets in each participant's project and then pull
workshop data from cloud object storage. The values for these credentials can be found
in the sample script [here](https://ibm-research.slack.com/archives/C083XGN35DM/p1742320250275449) 

To run the script to prepare the workshop environment for participants, perform the following: (these
steps were developed using python version 3.11))

```
# First, create a python virtualenv under the `.venv` directory
python -m virtualenv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the python requirements
pip install -r requirements.txt

# Run the workbench setup steps
python cluster_setup.py
```

If successful, you should see a series of messages like the following, one for each user listed
in [users_list.txt](users_list.txt):

```
Setting up environment for user $USERNAME
```

## OpenShift Cluster Setup

For this workshop, we'll use the [Red Hat OpenShift Servie on AWS (ROSA)](https://us-east-2.console.aws.amazon.com/rosa/home) service to create
the OpenShift cluster.

### Prerequisites

We first [downloaded the ROSA CLI](https://access.redhat.com/documentation/en-us/red_hat_openshift_service_on_aws/4/html/rosa_cli/rosa-get-started-cli) then logged into
the service via a `rosa login` command.

We then ran two one-time account setup commands to prepare the AWS account to host
a ROSA cluster:

```
rosa create account-roles --mode auto
rosa create network --region us-east-1
rosa create user-role
rosa create oidc-config --region us-east-1
```

### Cluster Creation

Run the following to create the cluster (*Note* The subnet IDs, OIDC config ID, and role ARNs used
here point to objects created by the above commands and will need to be changed if you are repeating
these steps in a different AWS account or region):

```
rosa create cluster \
  --cluster-name="summer-school" \
  --oidc-config-id="2hfkiaf9f330m4g2vhc87dggfnn11u8j" \
  --sts --mode=auto --hosted-cp \
  --subnet-ids=subnet-005cb7f923050f6c9,subnet-0ed35050f33a5fc68 \
  --compute-machine-type m6i.2xlarge \
  --role-arn="arn:aws:iam::340752805604:role/ManagedOpenShift-HCP-ROSA-Installer-Role" \
  --support-role-arn="arn:aws:iam::340752805604:role/ManagedOpenShift-HCP-ROSA-Support-Role" \
  --worker-iam-role="arn:aws:iam::340752805604:role/ManagedOpenShift-HCP-ROSA-Worker-Role"
```

You can check the status of the cluster creation with the following command:

```
rosa describe cluster -c summer-school
```

Once the `State` is listed as `Ready`, you have successfully created the cluster!

```
$ ./rosa describe cluster -c summer-school

Name:                       summer-school
Domain Prefix:              summer-school
Display Name:               summer-school

...Redacted

Managed Policies:           Yes
State:                      ready 
Private:                    No
Delete Protection:          Disabled
Created:                    Mar 12 2025 14:22:12 UTC
User Workload Monitoring:   Enabled
Details Page:               https://console.redhat.com/openshift/details/s/2uDi1o4nQTyaiyyncjFxUbaYeiD
OIDC Endpoint URL:          https://oidc.op1.openshiftapps.com/2hfkiaf9f330m4g2vhc87dggfnn11u8j (Managed)
Etcd Encryption:            Disabled
Audit Log Forwarding:       Disabled
External Authentication:    Disabled
Zero Egress:                Disabled
```

Next, add the GPU machine pool to the cluster: (Change the value of `replicas` based on how many
nodes you want. For the [g4dn.12xlarge](https://aws.amazon.com/ec2/instance-types/g4/)
 instance type, each node has 4 NVIDIA GPUs).)

```
rosa create machinepool \
  --cluster summer-school \
  --name gpu \
  --instance-type g4dn.12xlarge \
  --replicas 1
```

## Custom Workbench Image

To facilitate initializing a workbench environment for participants in which
all prerequisites are already installed, we'll use a custom workbench image for
this workshop.

The container file (AKA Dockerfile) for this workbench image can be found in
[workbench-notebook.CONTAINERFILE](workbench-notebook.CONTAINERFILE).

It was built with a command like:

```
podman build -t quay.io/accorvin/ai-for-good-workshop:v2 -f workbench-notebook.CONTAINERFILE .
```

Then pushed to Quay via:

```
podman push quay.io/accorvin/ai-for-good-workshop:v2
```

Then, an image stream was created on the OpenShift cluster to
make this workbench image available to individual workbenches by running the following
command:

```
cat <<EOF | oc apply -f -
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  annotations:
    opendatahub.io/notebook-image-desc: ""
    opendatahub.io/notebook-image-name: ai-for-good-workshop
    opendatahub.io/notebook-image-url: quay.io/accorvin/ai-for-good-workshop:v2
    opendatahub.io/recommended-accelerators: '["nvidia.com/gpu"]'
  labels:
    app.kubernetes.io/created-by: byon
    opendatahub.io/dashboard: "true"
    opendatahub.io/notebook-image: "true"
  name: ai-for-good-workshop
  namespace: redhat-ods-applications
spec:
  lookupPolicy:
    local: true
  tags:
  - annotations:
      opendatahub.io/notebook-python-dependencies: '[]'
      opendatahub.io/notebook-software: '[]'
      openshift.io/imported-from: quay.io/accorvin/ai-for-good-workshop:v2
    from:
      kind: DockerImage
      name: quay.io/accorvin/ai-for-good-workshop:v2
    generation: 2
    importPolicy:
      importMode: Legacy
    name: v2
    referencePolicy:
      type: Source
EOF
```

**Important** The image used for the workshop is specified in
[vars.yaml](vars.yaml) as workbench['image']. If you need to
change the image that is used, be sure to update this value.