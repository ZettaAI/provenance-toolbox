# provenance-toolbox
A set of basic utilities to standardize use of provenance files for pipeline documentation

When processing multiple connectomics datasets in parallel, keeping track of different contexts can be a challenge that slows down development and causes costly mistakes. [Cloud-volume's provenance files](https://github.com/seung-lab/cloud-volume/wiki/Provenance-Files) are capable of tracking the required information, but these have seen limited application partially due to their high degree of flexibility. These tools are an attempt to provide standardized ways of interacting with provenance files to guide their use and instill a set of requirements to define "properly-documented" processing.

This package defines two types of tools. The first are a set of classes to structure how to store information in and around provenance files. The second are 

#### Installation

```bash
pip install provenance-toolbox
```

#### Defined classes

The `Process` class attempts to define all of the information required to properly document a step of processing that creates or modifies a volume. That consists of 
1. A `description` field that names the process. This can be tweaked for multiple iterations of the same process (e.g., "meshing at 16x16x40 resolution", "meshing at 32x32x40 resolution"). This should be formatted as a `str`.
2. A dictionary of `parameters` that define how processing has occurred or will occur (`Union[dict, SimpleNamespace, ConfigParser]`).
4. A code environment (CodeEnv below)

A `CodeEnv` class defines a way to capture the state of a codebase and its environment to replicate processing. There are currently two `CodeEnv` classes implemented:
1. `PythonGithubEnv` describes a python codebase stored within a Github repository. It includes the repo URL, commit hash, and all usable packages within the current python environment.
2. `DockerEnv` describes a docker container using its image name, tag, and image ID (content hash). It will also store the current Python environment if desired using the `include_packages` flag.

The `Note` class defines a metadata note to log within a provenance file. It adds a timestamp and type (e.g., Motivation or Result) for easier viewing, though no viewing functions currently exist.

#### Usage

Once you've defined the classes above, provenance-tools defines a set of functions for logging them within a given CloudVolume
```python3
import provenancetoolbox as ptb
import cloudvolume as cv

volume = cv.CloudVolume(cloudpath)

# Defining a process
description = 'Properly documenting a process
parameters = {'prudence': 10/10}
code_env = ptb.PythonGithubEnv('.')  # path to the github repo directory

demoprocess = ptb.Process(description, parameters, code_env)

logprocess(cloudvolume, demoprocess)
```
Metadata about processes are logged in the provenance file of a given cloudvolume, and each code evironment is stored in separate code environment JSON files alongside the provenance file.

The `Note` objects are often handled implicitly in the background for you
```python3
ptb.addmotivation(cloudvolume, "Bootstrapping: adding segments 19&34")
ptb.addresult(cloudvolume, "Found more synapses")
ptb.addgeneric(cloudvolume, "Bizarre output in slice 37")
```
