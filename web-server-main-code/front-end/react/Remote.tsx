import * as React from 'react';
import axios from "axios";

// mui components
import {IconButton, Paper, Snackbar, Stack} from "@mui/material";

// mui icons
import CloseIcon from '@mui/icons-material/Close';
import ArrowUpwardRoundedIcon from '@mui/icons-material/ArrowUpwardRounded';
import ArrowDownwardRoundedIcon from '@mui/icons-material/ArrowDownwardRounded';
import StopRoundedIcon from '@mui/icons-material/StopRounded';

// bootstrap button
import Button from 'react-bootstrap/Button';

export enum Commands {
    Up = "up",
    Down = "down",
    Stop = "stop",
}

// handle triggering of remote control buttons
export const Remote = () => {
    // pop message state
    const [open, setOpen] = React.useState<string>("");
    const handleToastClose = (event: React.SyntheticEvent | Event, reason?: string) => {
        setOpen("");
    };

    // send remote message to backend server when buttons are clicked
    const handleClick = (action: Commands) => {
        axios.get(`api/remote/${action}`)
            // successful request
            .then(function (response) {
                console.log(response);
                console.log(response.statusText);

                // let the user know that it worked
                setOpen("Command sent");
            })
            // failed request
            .catch(function (error) {
                console.log(error);

                // let the user know that it failed
                setOpen(JSON.stringify(error.response));
            })
    }

    return (
        <>
            {/* pop up messages to let user know how the request went */}
            <Snackbar
                open={open?.length > 0}
                autoHideDuration={1000}
                onClose={handleToastClose}
                message={open}
                action={<IconButton
                    size="small"
                    aria-label="close"
                    color="inherit"
                    onClick={handleToastClose}
                >
                    <CloseIcon fontSize="small"/>
                </IconButton>}

            />

            {/* remote control buttons */}
            <Paper elevation={0} sx={{p: 4, borderRadius: 2, backgroundColor: 'rgba(255, 255, 255, 0.1)'}}>
                <Stack direction="row" justifyContent="center">
                    <Stack justifyContent="center" spacing={4}>
                        <Button
                            onClick={() => handleClick(Commands.Up)}
                            variant="light"
                            size="lg"
                        >
                            <Stack justifyContent="center" alignItems="center">
                                <ArrowUpwardRoundedIcon fontSize="large"/>
                                <strong>
                                    Up
                                </strong>
                            </Stack>
                        </Button>

                        <Button
                            onClick={() => handleClick(Commands.Stop)}
                            variant="dark"
                            size="sm"
                        >
                            <Stack justifyContent="center" alignItems="center" direction="row">
                                <StopRoundedIcon/>
                                <strong>
                                    Stop
                                </strong>
                            </Stack>
                        </Button>
                        <Button
                            onClick={() => handleClick(Commands.Down)}
                            variant="light"
                            size="lg"
                        >
                            <Stack justifyContent="center" alignItems="center">
                                <strong>
                                    Down
                                </strong>
                                <ArrowDownwardRoundedIcon fontSize="large"/>
                            </Stack>
                        </Button>
                    </Stack>
                </Stack>
            </Paper>
        </>
    )
}
