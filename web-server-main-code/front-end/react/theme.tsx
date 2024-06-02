import {createTheme} from '@mui/material/styles';
import {red} from '@mui/material/colors';

// MUI theme for the ROLLLIN app
const theme = createTheme({
    palette: {
        primary: {
            main: '#556cd6',
        },
        secondary: {
            main: '#19857b',
        },
        error: {
            main: red.A400,
        },
    },
});

export default theme;
