Safeget
-------

Download verified files, not malware. This is the most effective way to get your users to verify files.

With one command Safeget downloads <em>and</em> does the complex security checks that most people skip. Verifies pgp/gpg sigs, hashes, and more.

Description
-----------

Give them one command that downloads <em>and</em> verifies. They'll verify every time.

Safeget requires python3. If you see a "SyntaxError: invalid syntax", then you probably are tryinng to run safeget with python2.

Get Users to Always Verify Sigs and Hashes When They Download Files

With Safeget your users can download and carefully verify your files with a single command. They'll verify every time. And, you'll be confident that malware isn't being distributed under your name.

We all know our customers risk malware when they don't verify downloaded files. But it's so much hassle, most users skip it and hope for the best. Your own server logs show that.

Few people have any idea what a pgp/gpg sig or a hash is. People believe software should handle all that complex stuff. They're right.

Give them one command that downloads and verifies. They'll verify every time.

We can make it even simpler for your users, with free customized version for you that has your download url and verification data built in. No command line params. Just tell people to run it.

Safeget is free and open source.

Requirements
-------------

Safeget requires python3. You can run it on Windows, Linux, or Mac OS X.


Install
-------

If your operating system offers a safeget package, install it.

But safeget isn't in many package managers yet. Get it from CodeBerg with:

    git clone https://codeberg.org/topdevpros/safeget.git

Or download the safeget-installer and run it:

    python3 safeget-installer

Windows users: If you do not have GPG installed on your Windows computer, then you'll need to run Safeget as an administrator the first time you run it so that Safeget can install GPG onto your system. To open a command prompt as an administrator, start to search for "command prompt". An area near the search box appears with an option to "Execute as administrator". Select that option and then you can issue any Safeget command.


How it Works
------------

Your users just download the custom installer and run it. They don't have to install anything first. It's really hard to get it wrong.

You publish one command for your users that shows all the details. The more checks you specify, the safer your users are. It's good practice to publish your Safeget command through multiple channels.

Here's an example of using Safeget with one command for Bitcoin Core:

        safeget \
            https://bitcoin.org/bin/bitcoin-core-0.21.0/bitcoin-0.21.0-x86_64-linux-gnu.tar.gz \
            --pubkey https://raw.githubusercontent.com/bitcoin-core/bitcoincore.org/master/keys/laanwj-releases.asc \
            --signedhash SHA256:https://example.com/open/safeget/hashes/bitcoin-core-0.21.0/SHA256SUMS.asc

With either option, Safeget takes the same steps:

    1. Download the file
    2. Download public keys
    3. Import public keys
    4. Download signed messages with hashes
    5. Verify signed messages
    6. Verify file hashes

Most people skip everything after "Download the file". Safeget never does.

When a parameter is a url, Safeget searches that web page for what it needs. For example, a pgp signature can be buried in text. Safeget checks the protocol, downloads the page, and extracts the sig.

To make it even simpler for your users, we're happy to create a free customized version of Safeget for you. so your users just issue a one word command. No command line params. Your custom Safeget has your download and verification data embedded. Then just tell people to run your one word command.


Multiple Verification Methods
-----------------------------

Safeget checks:

    File source
        Secure connection
        Warns if keys and hashes are from same host
    Explicit hashes
        Ideally multiple hashes, because a collision with multiple modern hashes is extremely unlikely
    PGP/GPG file signatures
        Downloads and imports pgp public keys
        Downloads and verifies pgp file signatures
    Signed pgp/gpg messages containing hashes
        Downloads and verifies hash signatures
        Verifies the target file matches hashes
    File size


Why Safeget is secure
---------------------

Safeget solves the question of which verification sources and methods to trust: Don't trust any of them too much. The solution is a defense in depth, using multiple hosts and algorithms.

Safeget is completely decentralized with no gatekeeper. There's no single point of failure.

Because Safeget can check many hashes in addition to pgp/gpg signatures, it's highly resistant to quantum computing attacks.

    "Unlike many other signature systems, hash-based signatures would still be secure even if it proves feasible for an attacker to build a quantum computer." Internet Engineering Task Force - RFC 8554

Most file verification relies on a single host or algorithm. But no one really knows which ones are safe. Safeget checks as many as you like.

Safeget can get corroboration from multiple sources. Safeget can verify a file based on the file's source, pgp keys, pgp file signature, pgp signed hashes, explicit hashes, and more. You can spread the information across different hosts and use multiple hash algorithms. Everything has to agree for a file to verify.

 Sideloading, downloading files from unofficial sources, is risky. Safeget can make sideloading much safer.

Put your Safeget command on your own host.

You can specify as many checks as you like, all in one command. Then wrap it all in a simple custom safeget.

The more checks, the more certain you are that the file is valid. It is extremely unlikely that a bad file will pass multiple hash algorithms. You might find yourself calculating the time needed to find a multiple hash collision in HDOU units — "Heat Death of the Universe".

Of course, Safeget's not perfect. You still have the risk that someone cracks your own system. But since you are security conscious enough to encourage people to verify, you probably can protect your own system. Users are very likely to get your real Safeget and Safeget protects very effectively against MITM attacks.

In practice, when you use Safeget with multiple signed hashes attackers will have to bypass or attack Safeget itself.

Safeget is distributed as open source, in a single python file, so it's easy to audit the code. Please do.

Automatically install too

You can tell Safeget to run a program after it's done. It's a great way to launch installers. With one command you can download, verify thoroughly, and install.

Bugs

If you see a "SyntaxError: invalid syntax", then you probably are trying to run Safeget with python2. It's a bug in python2. Use python3.
With Safeget, users get your files, not malware

Most people don't verify. Maybe they don't quite understand how or why. Even security pros sometimes skip it.

Instead of telling your users to follow a long and complex procedure they'll often skip, download and verify with Safeget.

It doesn't matter if they don't know what a pgp/gpg sig or hash is. With Safeget, users verify files.

