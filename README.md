# sentinel1decoder
これはSentinel-1 Level0 ファイルのデコーダーを改造した研究用のレポジトリです。
フォーク元リポジトリはこちら：https://github.com/Rich-Hall/sentinel1decoder

## 使い方

Import the package:
```
import sentinel1decoder
```

New - Level0File class wraps most of the below functionality, while also breaking the file into bursts of constant swath number/number of quads, to allow for easy handling.

Initialize a Level0File object:
```
l0file = sentinel1decoder.Level0File( filename )
```

This class contains: a dataframe containing the packet metadata:
```
l0file.packet_metadata
```

A dataframe containing the ephemeris:
```
l0file.ephemeris
```

The metadata is indexed by burst as well as packet number. Metadata on individual bursts can be accessed via:
```
l0file.get_burst_metadata( burst )
```

The I/Q array for each burst can be generated via:
```
l0file.get_burst_data( burst )
```

Importantly, this data can now be cached in an `.npy` file using:
```
l0file.save_burst_data( burst )
```

--------------------------------------------

The individual decoding functions can still be used:

Initialize a Level0Decoder object:
```
decoder = sentinel1decoder.Level0Decoder( filename )
```

Generate a Pandas dataframe containing the header information associated with the Sentinel-1 downlink packets contained in the file:
```
df = decoder.decode_metadata()
```

Further decode the satellite ephemeris data from the information in the packet headers:
```
ephemeris = sentinel1decoder.utilities.read_subcommed_data(df)
```

Extract the data payload from the data packets in the file. Takes a Pandas dataframe as an input, and only decodes packets whose header is present in the input dataframe. The intended usage of this is to allow the user to select which packets to decode, rather than having to always decode the full file. For example, to decode the first 100 packets only:
```
selection = df.iloc[0:100]
iq_array = decoder.decode_packets(selection)
```
