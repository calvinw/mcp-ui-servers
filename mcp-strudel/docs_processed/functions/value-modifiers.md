# Control Parameters

Besides functions that control time, we saw earlier that functions like `note` and `cutoff` control different parameters (short params) of an event.
Let's now look more closely at how these `param(eter) functions` work.

# Parameter Functions

A very powerful feature of tidal patterns is that each parameter can be controlled independently:

```javascript
note("c a f e")
.cutoff("<500 1000 2000 [4000 8000]>")
.gain(.8)
.s('sawtooth')
.log()
```

In this example, the parameters `note`, `cutoff`, `gain` and `s` are controlled independently by either patterns or plain values (numbers / text).
After pressing play, we can observe the time and parameter values of each event (hap) in the output created by `.log()`.

## Plain vs Parameterized Values

Patterns that are not wrapped inside a param function will contain unlabeled `plain values`:

```javascript
"<c e g>".log()
```

This will not generate any sound output, because Strudel could only guess which param is meant by these letters.

Now compare that to the version wrapped in `note`:

```javascript
note("<c e g>").log()
```

Now it is clear that these letters are meant to be played as notes.
Under the hood, the `note` function (as well as all other param functions)
will wrap each plain value in an object. If the note function did not exist, we would need to write:



This will have the same output, though it is rather unwieldy to read and write.

## Wrapping Parameter Functions

To avoid too much nesting, param functions can also be chained like this:



This is equivalent to `note(cat('c','e','g')).log()`.

You can use this with any function that declares a type (like `n`, `s`, `note`, `freq` etc), just make sure to leave the parens empty!

## Plain Value Modification

Patterns of plain values can be modified with any of the following operators:

```javascript
"50 60 70".add("<0 1 2>").log()
```

Here, the add function modifies the numbers on the left.
Again, there is no output because these numbers have no meaning without a param.

## Param Value Modification

To modify a parameter value, you can either:

- Use the operator on the plain value pattern, inside the param function:

  ```javascript
note("50 60 70".add("<0 1 2>")).room(.1).log()
```

- Similarly, use the operator on the plain value pattern and wrap it later:

  ```javascript
"50 60 70".add("<0 1 2>").note().room(.1).log()
```

- Specify which param should be modified inside the operator function:

  ```javascript
note("50 60 70").room(.1).add(note("<0 1 2>")).log()
```

Remember the execution of the chained functions goes from left to right.

# Operators

This group of functions allows to modify the value of events.

## add

##Pattern.add##

*Function documentation for `Pattern.add`*

## sub

##Pattern.sub##

*Function documentation for `Pattern.sub`*

## mul

##Pattern.mul##

*Function documentation for `Pattern.mul`*

## div

##Pattern.div##

*Function documentation for `Pattern.div`*

## round

##Pattern.round##

*Function documentation for `Pattern.round`*

## floor

##Pattern.floor##

*Function documentation for `Pattern.floor`*

## ceil

##Pattern.ceil##

*Function documentation for `Pattern.ceil`*

## range

##Pattern.range##

*Function documentation for `Pattern.range`*

## rangex

##Pattern.rangex##

*Function documentation for `Pattern.rangex`*

## range2

##Pattern.range2##

*Function documentation for `Pattern.range2`*

## ratio

##Pattern.ratio##

*Function documentation for `Pattern.ratio`*

## as

##as##

*Function documentation for `as`*

# Custom Parameters

You can also create your own parameters:



Multiple params can also be created in a more consice way, using `createParams`:



Note that these params will not do anything until you give them meaning in your custom output!

From modifying parameters we transition to the concept of [Signals](/learn/signals).