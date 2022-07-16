# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 18:34:01 2022.

@author: richa
"""
import logging
from sentinel1decoder import constants


def decode_primary_header(header_bytes):
    """Decode the Sentinel-1 Space Packet primary header.

    Refer to SAR Space Protocol Data Unit specification document pg.13
    The primary header consists of exactly 6 bytes.

    Parameters
    ----------
    header_bytes : List
        List of input bytes. Must contain exactly 6 bytes.

    Returns
    -------
    output_dictionary : Dictionary
        Dictionary of primary header fields.

    """
    if not len(header_bytes) == 6:
        # TODO: Throw a proper error here
        logging.ERROR("Primary header must be exactly 6 bytes")

    tmp16 = int.from_bytes(header_bytes[:2], 'big')
    packet_version_number = tmp16 >> 13  # Bit 0-2
    packet_type = (tmp16 >> 12) & 0x01  # Bit 3
    secondary_header_flag = (tmp16 >> 11) & 0x01  # Bit 4
    process_id = (tmp16 >> 4) & 0x7f  # Bit 5-11
    packet_category = tmp16 & 0xf  # Bit 12-15

    tmp16 = int.from_bytes(header_bytes[2:4], 'big')
    sequence_flags = tmp16 >> 14  # Bit 0-1
    packet_sequence_count = tmp16 & 0x3f  # Bit 2-15

    tmp16 = int.from_bytes(header_bytes[4:], 'big')
    packet_data_length = tmp16+1  # Bit 0-15

    # Total space packet length must be a multiple of 4 bytes.
    # Packet length = 6 primary header bytes + packet data length
    if not (packet_data_length + 6) % 4 == 0:
        logging.error("Packet length is not a multiple of 4 bytes")

    output_dictionary = {
        "Packet Version Number": packet_version_number,
        "Packet Type": packet_type,
        "Secondary Header Flag": secondary_header_flag,
        "PID": process_id,
        "PCAT": packet_category,
        "Sequence Flags": sequence_flags,
        "Packet Sequence Count": packet_sequence_count,
        "Packet Data Length": packet_data_length
    }

    return output_dictionary


def decode_secondary_header(header_bytes):
    """Decode the Sentinel-1 Space Packet secondary header.

    Refer to SAR Space Protocol Data Unit specification document pg.14
    The secondary header consists of exactly 62 bytes.

    Parameters
    ----------
    header_bytes : List
        List of input bytes. Must contain exactly 62 bytes.

    Returns
    -------
    output_dictionary : Dictionary
        Dictionary of secondary header fields.

    """
    if not len(header_bytes) == 62:
        # TODO: Throw a proper error here
        logging.ERROR("Secondary header must be exactly 62 bytes")

    # ---------------------------------------------------------
    # Datation service (6 bytes)
    # ---------------------------------------------------------
    coarse_time = int.from_bytes(header_bytes[:4], 'big')

    fine_time = (int.from_bytes(header_bytes[4:6], 'big') + 0.5)*(2**(-16))

    output_dictionary = {
        "Coarse Time": coarse_time,
        "Fine Time": fine_time
    }

    # ---------------------------------------------------------
    # Fixed ancillary data field (14 bytes)
    # ---------------------------------------------------------
    sync = int.from_bytes(header_bytes[6:10], 'big')

    data_take_id = int.from_bytes(header_bytes[10:14], 'big')

    ecc_number = header_bytes[14]

    # Byte 15 bit 1 is unused
    test_mode = (header_bytes[15] >> 4) & 0x07  # Byte 15 Bits 1-3
    rx_channel_id = header_bytes[15] & 0x0f  # Byte 15 Bits 4-7

    instrument_config_id = int.from_bytes(header_bytes[16:20], 'big')

    output_dictionary.update({
        "Sync": sync,
        "Data Take ID": data_take_id,
        "ECC Number": ecc_number,
        "Test Mode": test_mode,
        "Rx Channel ID": rx_channel_id,
        "Instrument Configuration ID": instrument_config_id
    })

    if sync != 0x352EF853:
        logging.error("Sync marker != 352EF853")

    # ---------------------------------------------------------
    # Sub-commutated ancillary data service (3 bytes)
    # ---------------------------------------------------------
    # The update rate of satellite ephemeris data is much lower
    # than the space packet generation rate (up to 1Hz). Data is
    # thus subcommed in portions of 2 bytes per space packet.
    # The full data frame is 42 bytes long.
    subcom_data_word_ind = header_bytes[20]

    subcom_data_word = int.from_bytes(header_bytes[21:23], 'big')

    output_dictionary.update({
        "Sub-commutated Ancilliary Data Word Index": subcom_data_word_ind,
        "Sub-commutated Ancilliary Data Word": subcom_data_word
    })

    # ---------------------------------------------------------
    # Counters Service (8 bytes)
    # ---------------------------------------------------------
    space_packet_count = int.from_bytes(header_bytes[23:27], 'big')

    pri_count = int.from_bytes(header_bytes[27:31], 'big')

    output_dictionary.update({
        "Space Packet Count": space_packet_count,
        "PRI Count": pri_count
    })

    # ---------------------------------------------------------
    # Radar configuration support service (27 bytes)
    # ---------------------------------------------------------
    error_flag = header_bytes[31] >> 7  # Byte 31 Bit 0
    # Byte 31 Bits 1-2 are unused.
    baq_mode = header_bytes[31] & 0x1f  # Byte 31 Bits 3-7

    baq_block_length = header_bytes[32]

    # The byte at packet_data[33] is unused

    range_decimation = header_bytes[34]

    rx_gain = header_bytes[35]*-0.5

    tmp16 = int.from_bytes(header_bytes[36:38], 'big')
    txprr_sign = ((-1)**(1-(tmp16 >> 15)))
    txprr = txprr_sign*(tmp16 & 0x7fff)*(constants.f_ref**2)/(2**21)

    tmp16 = int.from_bytes(header_bytes[38:40], 'big')
    txpsf_additive = (txprr/(4*constants.f_ref))
    txpsf_sign = ((-1)**(1-(tmp16 >> 15)))
    txpsf = txpsf_additive+txpsf_sign*(tmp16 & 0x7fff)*constants.f_ref/(2**14)

    tmp24 = int.from_bytes(header_bytes[40:43], 'big')
    tx_pulse_length = tmp24/constants.f_ref

    # Byte 43 bits 0-2 are unused
    rank = header_bytes[43] & 0x1f  # Byte 43 bits 3-7

    tmp24 = int.from_bytes(header_bytes[44:47], 'big')
    pri = tmp24 / constants.f_ref

    tmp24 = int.from_bytes(header_bytes[47:50], 'big')
    sampling_window_start_time = tmp24 / constants.f_ref

    tmp24 = int.from_bytes(header_bytes[50:53], 'big')
    sampling_window_length = tmp24/constants.f_ref

    sas_ssbflag = header_bytes[53] >> 7  # Byte 53 Bit 0
    polarisation = (header_bytes[53] >> 4) & 0x07  # Byte 53 Bits 1-3
    temperature_comp = (header_bytes[53] >> 2) & 0x03  # Byte 53 Bits 4-5
    # Byte 53 Bits 6-7 are unused

    # Some extra unimplemented stuff here.
    # Exact fields used depends on the value of sas_ssbflag
    # TODO: Implement sas_ssb_message decoding

    calibration_mode = header_bytes[56] >> 6  # Byte 56 Bits 0-1
    # Byte 56 Bit 2 is unused
    tx_pulse_number = header_bytes[56] & 0x1f  # Byte 56 Bits 3-7

    signal_type = header_bytes[57] >> 4  # Byte 57 Bits 0-3
    # Byte 57 Bits 4-6 are unused
    swap_flag = header_bytes[57] & 0x01  # Byte 57 Bit 7

    swath_number = header_bytes[58]

    output_dictionary.update({
        "Error Flag": error_flag,
        "BAQ Mode": baq_mode,
        "BAQ Block Length": baq_block_length,
        "Range Decimation": range_decimation,
        "Rx Gain": rx_gain,
        "Tx Ramp Rate": txprr,
        "Tx Pulse Start Frequency": txpsf,
        "Tx Pulse Length": tx_pulse_length,
        "Rank": rank,
        "PRI": pri,
        "SWST": sampling_window_start_time,
        "SWL": sampling_window_length,
        "SAS SSB Flag": sas_ssbflag,
        "Polarisation": polarisation,
        "Temperature Compensation": temperature_comp,
        "Calibration Mode": calibration_mode,
        "Tx Pulse Number": tx_pulse_number,
        "Signal Type": signal_type,
        "Swap Flag": swap_flag,
        "Swath Number": swath_number
    })

    # ---------------------------------------------------------
    # Radar sample count service (3 bytes)
    # ---------------------------------------------------------
    number_of_quads = int.from_bytes(header_bytes[59:61], 'big')

    # The byte at packet_data[61] is unused

    output_dictionary.update({
        "Number of Quads": number_of_quads
    })

    # ---------------------------------------------------------
    # End of secondary header information
    # ---------------------------------------------------------

    return output_dictionary