# espeak-ng_german_loan_words

In this brief tutorial with code you can automatically create a dictionary with **~10k German loan words** for import into [espeak-ng](https://en.wikipedia.org/wiki/ESpeak#eSpeak_NG) 
as additional phonemic improvement or extension. This is, for instance, useful with Text-to-Speech (TTS) tasks in order to improve preprocessing.

The data comes from the German [Wiktionary](https://de.wiktionary.org/wiki/Wiktionary:Hauptseite) as XML contents and
is automatically parsed. It contains [IPA codes](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet) for these loan words which however are not
directly usable with espeak-ng since it uses a "reduced" version in ASCII format, called [Kirshenbaum](https://en.wikipedia.org/wiki/Kirshenbaum).

For these reasons, IPA codes are automatically converted into compatible espeak-ng encodings using the KirshenbaumMapper by external library [ipapy](https://pypi.org/project/ipapy).

As a result, an output file `de_extra` is generated which can be imported into espeak-ng directly.

## Step-by-Step Tutorial

**[1]** Most of the processing is done inside a Docker container. Please start with building the container from the repository's directory (after cloning this repository, of course):

```
docker build --rm -t espeak-ng_german_loan_words .
```

It installs all programmatic files but does **NOT** download data at this point!

**[2]** After successfully building the container you can run it any time by typing (**Please note**: You need to specify `<output_directory>` 
where the output file is eventually placed on your local machine):

```
docker run --rm -v <output_directory>:/wik_out espeak-ng_german_loan_words
```

*Note: You can try to run with your local user and group as parameter (`-u $(id -u):$(id -g)`) so that the resulting file `de_extra` is not saved as `root` user and group. But you may encounter problems when downloading the wiktionary file (`permission denied`) then.*


This first downloads the most recent version of the German wiktionary, decompresses the file and
starts parsing and generating the output file for the espeak-ng import later.

Please note, depending on your connection this may take a while for downloading and depending on
the speed of your CPU, decompressing and parsing/generating might also take a couple of minutes.

**[3]** During parsing the XML data or converting IPA codes to espeak-ng encodings there might be
some warnings or error messages from failing encodings. The process usually runs smoothly and all
terms causing (possible) issues are logged to an extra tabular file, called `issue_terms.tab` which is to be
found in the same ouput directory as file `de_extra`

You can first of all ignore that file or use it to specifically filter the output file `de_extra`: If a term is
**possibly** causing trouble but included in the output file the respective column *status* is set to *included*.
Otherwise, if some term was not put into the output, it says *excluded*.

Also loan words which still lack an IPA code in Wiktionary are put there and the respective column *ipa_code*
is set to *not available*.

**[4]** The last step is to import the file into espeak-ng given you have installed it correctly to your system:

a) You first need to also copy the file for rules `de_rules` to the **same** directory as `de_extra`.

This file is available from the espeak-ng repo here:

`wget https://raw.githubusercontent.com/espeak-ng/espeak-ng/master/dictsource/de_rules`

b) Secondly, import is simply done via changing to the output directory (where `de_extra` and `de_rules` are located)
and running (in case, use `sudo` if necessary depending on your linux distribution)

```espeak-ng --compile=de```

**[5]** Unfortunately, the process can not be fully automatic since at this step we *may* get a small number of "Compile errors".
This is not as bad as it sounds, though.

Please recall the file *issue_terms.tab* from [3] above: You might simply remove all entries from this file which are *included* in the
`issue_terms.tab` file -- this should solve most of the compile errors and makes sure the phonemic encodings which are actually imported work as expected!

Or you remove simply those terms causing compile errors. 
This is probably the best thing you can do, if you don't want to get into working with/manually fixing the encodings.

## Bugs/Issues

Please let me know by filing github issues about any bugs or issues you encounter. Thanks.
