# HyperpodCLI

This is a Python3 project.

## Choosing your Python version

### Using CPython3

Build the following package major version/branches into your versionset:

* `Python-`**`default`** : `live`
* `CPython3-`**`default`** : `live`


This will cause `bin/python` to run `python3.7` as of 03/2020 but over time this
version will be kept up to date with the current best practice interpreters.

Your default interpreter is always enabled as a build target for python packages in your version set.

You should build the `no` branches for all interpreters into your versionset as
well, since the runtime interpreter will always build:

* `CPython27-`**`build`** : `no`
* `CPython34-`**`build`** : `no`
* `CPython36-`**`build`** : `no`
* `CPython37-`**`build`** : `no`
* `CPython38-`**`build`** : `no`
* `Jython27-`**`build`** : `no`

(Note that many of these are off in `live` already)

### Using a newer version of CPython3

If you need a special version of CPython (say you want to be on the cutting edge and use 3.9):

* `Python-`**`default`** : `live`
* `CPython3-`**`default`** : `CPython39`

This will cause `bin/python` to run `python3.9`

### Using CPython2 2.7 or Jython

**Don't**

## Building

Modifying the build logic of this package just requires overriding parts of the
setuptools process. The entry point is either the `release`, `build`, `test`, or
`doc` commands, all of which are implemented as setuptools commands in
the package.


#### Best practices for filtering

1. Use forwards-compatible filters (i.e. `$version -ge 37`).  This will make it painless to test and update when you update your default
2. Don't tie to older versions.  This is expensive technical debt that paying it down sooner is far better than chaining yourself (and your consumers) to older interpreters
3. If you want to specifically only build for the default interpreter, you can add the filter `[[ $1 == "$(default-python-package-name)" ]] || exit 1`
  1. **Only do this if you intend to vend an executable that is specifically getting run with the default interpreter, for integration test packages, or for packages that only should be built for a single interpreter (such as a data-generation or activation-scripts package)**

## Testing

Use `pytest` to run unit tests