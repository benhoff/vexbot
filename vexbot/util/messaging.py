from zmq.utils.interop import cast_int_addr

def get_addresses(message: list) -> list:
    """
    parses a raw list from zmq to get back the components that are the address
    messages are broken by the addresses in the beginning and then the
    message, like this: ```addresses | '' | message ```
    """
    # Need the address so that we know who to send the message back to
    addresses = []
    for address in message:
        # if we hit a blank string, then we've got all the addresses
        if address == b'':
            break
        addresses.append(address)

    return addresses
