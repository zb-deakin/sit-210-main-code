import * as React from 'react';

// MUI icons
import LightModeRoundedIcon from '@mui/icons-material/LightModeRounded';
import WaterDropRoundedIcon from '@mui/icons-material/WaterDropRounded';
import ThermostatRoundedIcon from '@mui/icons-material/ThermostatRounded';

// components from MUI and Bootsrap libraries
import {Box, Container, Paper, Stack, SxProps, Theme} from "@mui/material";
import Button from "react-bootstrap/Button";

// remote control component
import {Remote} from "./Remote";

// white background container
const automationStyle: SxProps<Theme> = {
    p: 2,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    color: "white",
    fontSize: "1.25rem",
}
export const Well = ({children}) => <Paper elevation={0} sx={automationStyle}>{children}</Paper>

// main application
export const App = () => {
    return (
        <Box sx={{color: "white"}}>
            <Box sx={{backgroundColor: "rgba(0, 0, 0, 0.05)"}}>
                <Container className="nunito-sans" maxWidth="lg" sx={{py: 2}}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2}
                           flexWrap="wrap">
                        <h1 style={{color: 'white'}}>
                            <strong style={{fontWeight: 900, fontSize: "1.5em"}}>
                                <em>
                                    ROLLLIN
                                </em>
                            </strong>
                        </h1>
                        <Box>
                            <Stack direction="row" gap={2} flexWrap="wrap">
                                <Button variant="light">Dashboard</Button>
                                <Button variant="light">My account</Button>
                            </Stack>
                        </Box>
                    </Stack>
                </Container>
            </Box>
            <Container maxWidth="lg" sx={{py: 2}}>
                <h3 style={{color: 'rgba(0, 0, 120, 0.65)', fontSize: "2rem", marginBottom: "2rem"}}>
                    Dashboard
                </h3>
                <Stack spacing={1}>
                    <h1>
                        <strong>
                            SUNROOM BLINDS
                        </strong>
                    </h1>
                    <Stack
                        direction="row"
                        justifyContent="stretch"
                        alignItems="stretch"
                        flexWrap="wrap"
                        gap={4}
                        sx={{pt: 1}}
                    >
                        <Stack spacing={2}>
                            <h4>Remote</h4>
                            <Remote/>
                        </Stack>
                        <Stack spacing={2} justifyContent="stretch" alignItems="stretch">
                            <h4>Automations</h4>
                            <Well>
                                <Stack spacing={2}>
                                    <Well>
                                        <Stack direction="row" gap={2} alignItems="center" flexWrap="wrap">
                                            <ThermostatRoundedIcon/>
                                            Close every day
                                            <strong>25° Celsius</strong>
                                        </Stack>
                                    </Well>
                                    <Well>
                                        <Stack direction="row" gap={2} alignItems="center" flexWrap="wrap">
                                            <WaterDropRoundedIcon/>
                                            Close every day
                                            <strong>Humidity 80%</strong>
                                        </Stack>
                                    </Well>
                                    <Well>
                                        <Stack direction="row" gap={2} alignItems="center" flexWrap="wrap">
                                            <LightModeRoundedIcon/>
                                            Close every day
                                            <strong>BRIGHT SUN</strong>
                                        </Stack>
                                    </Well>
                                </Stack>
                            </Well>
                        </Stack>
                    </Stack>
                </Stack>
            </Container>
        </Box>
    )
}
