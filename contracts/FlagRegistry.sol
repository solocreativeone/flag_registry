// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title FlagRegistry
/// @notice A public, permissionless on-chain registry of reputation flags on
///         addresses. Anyone can flag an address with a reason and severity;
///         anyone can read every flag ever placed on an address. Off-chain
///         services (bots, dashboards, other dApps) listen for the emitted
///         events and use them to power alerts, scoring, or trust decisions —
///         without relying on one company's private database.
contract FlagRegistry {
    enum Severity {
        Info,       // 0 - informational, no risk implied
        Low,        // 1
        Medium,     // 2
        High        // 3 - high-confidence risk signal
    }

    struct Flag {
        address flaggedBy;
        bytes32 reason;
        Severity severity;
        uint256 timestamp;
    }

    // target address => all flags ever placed on it
    mapping(address => Flag[]) private _flagsOn;

    event AddressFlagged(
        address indexed target,
        address indexed flaggedBy,
        bytes32 reason,
        Severity severity,
        uint256 timestamp
    );

    error ZeroAddress();

    /// @notice Place a flag on `target`. Flags are permanent and append-only —
    ///         reputation history should not be editable by any single party,
    ///         including the original flagger.
    /// @param target The address being flagged.
    /// @param reason A short machine-readable reason code (e.g. keccak256("LARGE_OUTFLOW")
    ///        or a padded human-readable string cast to bytes32).
    /// @param severity How serious this flag is.
    function flag(address target, bytes32 reason, Severity severity) external {
        if (target == address(0)) revert ZeroAddress();

        _flagsOn[target].push(
            Flag({flaggedBy: msg.sender, reason: reason, severity: severity, timestamp: block.timestamp})
        );

        emit AddressFlagged(target, msg.sender, reason, severity, block.timestamp);
    }

    /// @notice Returns every flag ever placed on `target`, in the order they were added.
    function getFlags(address target) external view returns (Flag[] memory) {
        return _flagsOn[target];
    }

    /// @notice Returns how many flags `target` has accumulated.
    function getFlagCount(address target) external view returns (uint256) {
        return _flagsOn[target].length;
    }

    /// @notice Returns the highest severity ever recorded on `target`.
    ///         Returns Severity.Info (0) if there are no flags.
    function getHighestSeverity(address target) external view returns (Severity) {
        Flag[] storage flags = _flagsOn[target];
        Severity highest = Severity.Info;

        for (uint256 i = 0; i < flags.length; i++) {
            if (flags[i].severity > highest) {
                highest = flags[i].severity;
            }
        }

        return highest;
    }
}
