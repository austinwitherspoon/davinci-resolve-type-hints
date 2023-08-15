# davinci-resolve-type-hints

An attempt and "automatically" generating DaVinci Resolve python stubs. This will add in auto-complete and type checking to any code that uses Resolve's python API.

Currently built off of Resolve 18.5
Very fast and dirty at the moment.

Drop Resolve's developer documentation README.txt into `original_resolve_docs` and run `generate_resolve_type_hints.py`.

If you're just looking for the stubs file, check out the [latest release page](https://github.com/austinwitherspoon/davinci-resolve-type-hints/releases/tag/latest). Download this .pyi file and place it in the `typings/` folder in your repo (or wherever you want, if you've configured your IDE differently!)
